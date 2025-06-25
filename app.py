import streamlit as st
import pandas as pd

# Import functions from the new modules
from state_helpers import initialize_session_state
from ui_controls import (
    display_file_uploader, 
    display_filter_controls_in_main, 
    display_save_load_filter_sets_controls
)
from filter_processing import apply_filters_to_dataframe

# Initialize session state ONCE at the very beginning
initialize_session_state() # Sua função existente para inicializar o estado da app

import streamlit as st # Mover import para o topo se ainda não estiver lá por completo
from streamlit_cookies_manager import EncryptedCookieManager # Importar
import datetime # Para timedelta, embora não usado diretamente aqui, mas relacionado

# --- Configuração do Cookie Manager (repetida para cada página protegida ou app.py) ---
# Idealmente, isso poderia ser encapsulado se você tiver muitas páginas.
try:
    encryption_key = st.secrets["cookies"]["encryption_key"]
    if encryption_key == "PLEASE_REPLACE_WITH_A_REAL_GENERATED_FERNET_KEY" or len(encryption_key) < 32:
        st.error("A chave de criptografia de cookies em .streamlit/secrets.toml não é válida ou é um placeholder.")
        st.stop()
except (KeyError, FileNotFoundError):
    st.error("Chave de criptografia para cookies ('cookies.encryption_key') não encontrada em .streamlit/secrets.toml.")
    st.stop()

cookies = EncryptedCookieManager(key=encryption_key) # prefix pode ser adicionado se desejado


APP_TITLE = "Filtro Dinâmico e Análise de Arquivos"

# Page Configuration - deve ser a primeira chamada Streamlit real
# Se initialize_session_state() não faz chamadas Streamlit, está OK.
# Se cookies.ready() for necessário antes de st.set_page_config, a ordem pode precisar de ajuste.
# Geralmente, st.set_page_config() é a primeira.
if cookies.ready(): # Só chame st.set_page_config se os cookies estiverem prontos (melhor prática)
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="expanded" 
    )

# --- Lógica de Restauração de Sessão via Cookie ---
def restore_session_from_cookie():
    if not cookies.ready():
        return # Não pode fazer nada se o gerenciador não estiver pronto

    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        # Tentar carregar o nome de usuário do cookie
        # O nome do cookie é 'user_session_token' como definido na página de login
        username_from_cookie = cookies.get('user_session_token')
        if username_from_cookie:
            # Se o cookie existir e tiver um valor, consideramos o usuário logado.
            # Em um sistema mais complexo, você validaria este token/username contra um backend.
            st.session_state.logged_in = True
            st.session_state.username = username_from_cookie
            # Não precisa de rerun aqui, pois isso acontece antes da renderização principal da página.
        # else: O cookie não existe ou está vazio, então o usuário não está logado via cookie.

restore_session_from_cookie() # Chamar para tentar restaurar a sessão

# --- Main Application Logic (Página Principal) ---
def main_page():
    st.title(APP_TITLE)

    # File uploader will use the default key: "default_file_uploader_widget"
    display_file_uploader() 
    
    current_df = st.session_state.get('df')

    # --- Sidebar for Save/Load Operations ---
    # This will make these controls appear in the Streamlit sidebar when this page is active
    with st.sidebar:
        st.header("Gerenciar Filtros") # Changed from "Gerenciar Filtros Ativos" for clarity
        display_save_load_filter_sets_controls()

    if current_df is not None and not current_df.empty:
        active_filters = st.session_state.get('filters', [])
        df_filtered = apply_filters_to_dataframe(current_df, active_filters)

        st.subheader("📊 Visualização dos Dados")
        st.dataframe(df_filtered, height=300) 
        st.markdown(f"**Resumo:** Original: `{len(current_df)}` linhas | Filtrado: `{len(df_filtered)}` linhas")

        display_filter_controls_in_main(list(current_df.columns))

        if active_filters:
            with st.expander("Ver Definição JSON dos Filtros Ativos", expanded=False):
                st.json(active_filters) 
    else:
        st.info("✨ Bem-vindo! Carregue um arquivo (XLSX, CSV, ODS) para começar.")

if __name__ == "__main__":
    # A inicialização de st.session_state.logged_in/username agora é coberta por
    # initialize_session_state() e/ou restore_session_from_cookie().
    # A verificação principal é se st.session_state.logged_in é True.

    if st.session_state.get('logged_in', False):
        if st.session_state.username: # Adicionar uma saudação se logado
             st.sidebar.success(f"Logado como: {st.session_state.username}")
        main_page()
    else:
        st.warning("⚠️ Por favor, faça login para acessar a aplicação.")
        st.page_link("pages/01_Login.py", label="Ir para a Página de Login", icon="🔒")
        st.info("Se você acabou de se registrar ou fazer login, a página pode precisar ser recarregada "
                "ou navegada novamente para refletir o estado de login em todas as partes da aplicação, "
                "especialmente se os cookies estiverem sendo estabelecidos.") # Nota para o usuário
