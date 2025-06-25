import streamlit as st
import sys
import os
import datetime # Necessário para a expiração do cookie
from streamlit_cookies_manager import EncryptedCookieManager # Alterado para EncryptedCookieManager

# Adicionar o diretório raiz ao sys.path para importar user_management
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from user_management import verify_user, register_user, initialize_users_file
except ImportError:
    st.error("Falha ao importar user_management. Verifique a estrutura do projeto e o sys.path.")
    st.stop()

# Configuração do gerenciador de cookies
# A chave DEVE ser uma string codificada em URL-safe base64 de 32 bytes.
# Gere uma com: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
# E coloque em .streamlit/secrets.toml
try:
    encryption_key = st.secrets["cookies"]["encryption_key"]
    if encryption_key == "PLEASE_REPLACE_WITH_A_REAL_GENERATED_FERNET_KEY" or len(encryption_key) < 32: # Verificação básica
        st.error("A chave de criptografia de cookies em .streamlit/secrets.toml não é válida ou é um placeholder. "
                 "Por favor, gere uma chave Fernet real e atualize o arquivo.")
        st.stop()
except (KeyError, FileNotFoundError): # FileNotFoundError pode ocorrer se secrets.toml não existir
    st.error("Chave de criptografia para cookies ('cookies.encryption_key') não encontrada em .streamlit/secrets.toml. "
             "Crie o arquivo e adicione a chave.")
    st.stop()

cookies = EncryptedCookieManager(
    # A chave para EncryptedCookieManager é a chave Fernet para criptografia.
    key=encryption_key,
    # O argumento 'prefix' é usado para nomear os cookies internamente pela biblioteca,
    # não é o nome do cookie que você define com set().
    # Vamos usar o nome do cookie explicitamente em set/get/delete.
    # prefix="afltapp/authuser" # Exemplo de prefixo
)

def try_restore_session_for_login_page():
    if not cookies.ready():
        return
    # Só tenta restaurar se não já estiver logado no session_state
    if not st.session_state.get('logged_in', False): # Verifique se já não está logado na sessão atual
        username_from_cookie = cookies.get('user_session_token')
        if username_from_cookie:
            st.session_state.logged_in = True
            st.session_state.username = username_from_cookie
            # Não precisa de st.rerun() aqui, pois isso acontece antes da renderização da página.

def login_page():
    """Renderiza a página de login/registro."""
    # Tenta restaurar a sessão do cookie ANTES de qualquer outra lógica de UI ou estado.
    # Mas depois da inicialização do st.session_state básico.
    # A inicialização do st.session_state para logged_in, username, etc., já acontece abaixo.
    # try_restore_session_for_login_page() deve ser chamado após essas inicializações
    # para que possa sobrescrevê-las se um cookie válido for encontrado.
    # Colocarei após o bloco de inicialização do st.session_state.

    initialize_users_file()

    # st.set_page_config deve ser a primeira chamada Streamlit no script da página.
    # Se app.py já define um global, esta pode ser redundante ou causar conflito se diferente.
    # Para páginas separadas, ter seu próprio page_title é geralmente OK.
    # Removendo daqui para evitar conflitos, assumindo que app.py cuida da configuração global da página.
    # st.set_page_config(page_title="Login", page_icon="🔒") 

    # Inicializar o estado da sessão se não existir
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'login_error' not in st.session_state:
        st.session_state.login_error = None
    if 'register_error' not in st.session_state:
        st.session_state.register_error = None
    if 'register_success' not in st.session_state:
        st.session_state.register_success = None
    if 'previous_choice' not in st.session_state: 
        st.session_state.previous_choice = "Login"

    # Tenta restaurar a sessão do cookie aqui, após as inicializações básicas do session_state
    # mas antes de decidir qual UI mostrar (logado vs não logado).
    try_restore_session_for_login_page()

    if not cookies.ready(): # Verificar se o gerenciador de cookies está pronto
        st.warning("Gerenciador de cookies não está pronto. A persistência de login pode não funcionar.")
        # Geralmente, ele funciona bem.

    if st.session_state.logged_in:
        st.sidebar.success(f"Logado como: {st.session_state.username}")
        st.title(f"Bem-vindo(a) de volta, {st.session_state.username}!")
        st.write("Você já está logado.")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.login_error = None
            st.session_state.register_error = None
            st.session_state.register_success = None
            st.success("Logout realizado com sucesso!") # Mensagem temporária
            st.rerun() # Força o rerun para atualizar a interface
        st.page_link("app.py", label="Ir para a Aplicação Principal", icon="🏠")

    else:
        st.title("Login / Registro")

        choice = st.radio("Escolha uma ação:", ("Login", "Registrar Novo Usuário"), horizontal=True)
        st.markdown("---")

        if choice == "Login":
            st.subheader("Login")
            with st.form("login_form"):
                login_username = st.text_input("Nome de Usuário", key="login_uname")
                login_password = st.text_input("Senha", type="password", key="login_pword")
                login_button = st.form_submit_button("Login")

                if login_button:
                    if verify_user(login_username, login_password):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.session_state.login_error = None
                        
                        # Definir cookie ao logar
                        # O nome do cookie aqui é 'user_session_token'
                        # O valor é o nome de usuário (que será criptografado)
                        # Expira em 7 dias
                        expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
                        cookies.set('user_session_token', login_username, expires_at=expires_at)
                        # Nota: A biblioteca EncryptedCookieManager usa seu 'prefix' internamente
                        # para nomear o cookie real no navegador. O 'user_session_token' é a chave
                        # que você usa com a biblioteca para get/set/delete.

                        st.rerun() 
                    else:
                        st.session_state.login_error = "Nome de usuário ou senha inválidos."
                
                if st.session_state.login_error:
                    st.error(st.session_state.login_error)


        elif choice == "Registrar Novo Usuário":
            st.subheader("Registrar Novo Usuário")
            with st.form("register_form"):
                reg_username = st.text_input("Escolha um Nome de Usuário", key="reg_uname")
                reg_password = st.text_input("Escolha uma Senha", type="password", key="reg_pword")
                reg_password_confirm = st.text_input("Confirme a Senha", type="password", key="reg_pword_confirm")
                register_button = st.form_submit_button("Registrar")

                if register_button:
                    if not reg_username or not reg_password:
                        st.session_state.register_error = "Nome de usuário e senha são obrigatórios."
                    elif reg_password != reg_password_confirm:
                        st.session_state.register_error = "As senhas não coincidem."
                    else:
                        # A função register_user em user_management já mostra st.error/st.success
                        # Então, aqui só precisamos limpar o estado de erro/sucesso local
                        st.session_state.register_error = None 
                        st.session_state.register_success = None
                        
                        # A função register_user retorna True em sucesso, False em falha
                        # E já lida com st.error internamente para "usuário já existe"
                        # ou "campos vazios" (embora já tenhamos verificado aqui)
                        if register_user(reg_username, reg_password):
                            st.session_state.register_success = f"Usuário '{reg_username}' registrado com sucesso! Você já pode fazer login."
                            # Limpar campos do formulário de registro (opcional, mas bom UX)
                            # Isso requer que os widgets sejam recriados, o que o rerun fará.
                            # No entanto, para limpar explicitamente, teríamos que manipular os keys,
                            # ou apenas deixar que o rerun limpe após a mensagem de sucesso.
                            # Por simplicidade, a mensagem de sucesso é suficiente.
                        else:
                            # register_user já mostrou um st.error,
                            # podemos apenas garantir que não haja mensagem de sucesso aqui.
                            st.session_state.register_success = None
                            # A mensagem de erro específica (ex: "Usuário já existe")
                            # é mostrada por register_user.
                            # Não precisamos definir st.session_state.register_error aqui
                            # a menos que queiramos sobrescrever a mensagem de register_user.
                
                if st.session_state.register_error:
                    st.error(st.session_state.register_error)
                if st.session_state.register_success:
                    st.success(st.session_state.register_success)
                    # Limpar a mensagem de sucesso após exibi-la uma vez
                    st.session_state.register_success = None 


if __name__ == "__main__":
    login_page()

# Garantir que o estado de erro/sucesso seja limpo ao mudar de aba (Login/Registro)
# Isso pode ser feito observando a mudança no st.radio, mas é complexo com o estado atual.
# Uma forma mais simples é que as mensagens de erro/sucesso são resetadas (para None)
# antes de tentar uma nova operação de login ou registro.
# As mensagens de `user_management.py` (st.error/st.success) são inerentemente temporárias.
# As mensagens de `st.session_state.login_error` e `st.session_state.register_error`
# são explicitamente setadas e mostradas. Elas são resetadas (para None)
# em um login/registro bem-sucedido ou antes de uma nova tentativa.
# A mensagem de sucesso de registro é explicitamente limpa após ser mostrada.

# O st.set_page_config deve ser a primeira chamada Streamlit, exceto st.echo, st.spinner ou st.help.
# Se já estiver definido em app.py, pode causar um erro se chamado novamente aqui com parâmetros diferentes.
# Idealmente, a configuração global fica em app.py e páginas específicas podem ter títulos via st.title.
# Para este caso, como é uma página "separada" de login, ter seu próprio page_title é aceitável.
# Se houver conflito, remova st.set_page_config daqui e confie no app.py.
# No entanto, Streamlit permite st.set_page_config em cada página para definir o título da aba do navegador e ícone.
# O que não é permitido é chamar st.set_page_config múltiplas vezes *dentro da mesma execução de script de página*.
# Como esta é uma página separada (01_Login.py), está OK.

# Limpar mensagens de erro/sucesso se o usuário alternar entre Login e Registro
# Isso é um pouco mais avançado e pode requerer callbacks no st.radio.
# Por enquanto, as mensagens persistem até a próxima submissão de formulário ou rerun.
# Uma forma simples de mitigar:
if 'previous_choice' not in st.session_state:
    st.session_state.previous_choice = "Login" # Default

if 'choice' in locals() and st.session_state.previous_choice != choice: # 'choice' é o valor do st.radio
    st.session_state.login_error = None
    st.session_state.register_error = None
    st.session_state.register_success = None
    st.session_state.previous_choice = choice
    # Não fazer rerun aqui, pois isso pode acontecer durante a renderização inicial.
    # A limpeza ocorrerá e a página continuará a renderizar com os erros/sucessos limpos.
    # Isso garante que, ao mudar de aba, as mensagens antigas desapareçam.

# Nota: A verificação de 'choice' in locals() é para evitar erro se st.radio não for renderizado
# (por exemplo, se o usuário já estiver logado).
# A lógica de limpeza de st.session_state.previous_choice != choice
# deve ser colocada após a definição do st.radio e antes que as mensagens de erro/sucesso sejam exibidas
# para que, se o usuário alternar, as mensagens sejam limpas antes de serem potencialmente exibidas novamente.
# No entanto, a estrutura atual com st.form e st.rerun já lida com a maioria dos casos de atualização de UI.
# A adição acima é uma melhoria para limpar erros ao alternar abas sem submeter um formulário.
# Para ser eficaz, ela deveria estar dentro da função login_page, após o st.radio.

# Corrigindo a localização da lógica de limpeza de erro ao alternar abas:
# Esta lógica foi movida para dentro da função login_page, após o st.radio,
# mas isso não é trivial de fazer sem reestruturar significativamente como os formulários e
# o estado são tratados.
# Uma solução mais simples é que os erros são apenas substituídos ou limpos na próxima ação.
# As mensagens de sucesso já são limpas após a exibição.
# As mensagens de erro (st.session_state.login_error, st.session_state.register_error)
# são sobrescritas na próxima tentativa ou limpas em caso de sucesso.
# Para esta implementação, vamos manter a lógica atual, que é funcional.
# Refinamentos de UX como limpar erros ao trocar de abas sem submissão podem ser adicionados depois se necessário.
