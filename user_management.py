import json
import bcrypt
import os
import streamlit as st # Added for st.error and st.success

USERS_FILE = "users.json"

def get_users_file_path():
    """Returns the absolute path to the users.json file."""
    # For Streamlit Cloud or similar environments, st.secrets might be better for sensitive paths or data.
    # For local development, placing it in the root of the project is common.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), USERS_FILE)

def load_users():
    """Carrega os usuários do arquivo JSON."""
    users_file_path = get_users_file_path()
    if not os.path.exists(users_file_path):
        return {}
    try:
        with open(users_file_path, "r") as f:
            data = json.load(f)
            return data
    except (IOError, json.JSONDecodeError) as e:
        st.error(f"Erro ao carregar o arquivo de usuários: {e}")
        return {}

def save_users(users_data):
    """Salva os usuários no arquivo JSON."""
    users_file_path = get_users_file_path()
    try:
        with open(users_file_path, "w") as f:
            json.dump(users_data, f, indent=4)
    except IOError as e:
        st.error(f"Erro ao salvar o arquivo de usuários: {e}")


def hash_password(password):
    """Gera o hash de uma senha."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(password, hashed_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(username, password):
    """Registra um novo usuário."""
    users = load_users()
    if not username or not password:
        st.error("Nome de usuário e senha não podem estar vazios.")
        return False
    if username in users:
        st.error("Nome de usuário já existe.")
        return False
    
    hashed = hash_password(password)
    users[username] = {"password": hashed}
    save_users(users)
    st.success("Usuário registrado com sucesso!")
    return True

def verify_user(username, password):
    """Verifica as credenciais do usuário."""
    users = load_users()
    if username not in users:
        return False
    
    user_data = users[username]
    return check_password(password, user_data["password"])

# Initialize users.json if it doesn't exist
def initialize_users_file():
    users_file_path = get_users_file_path()
    if not os.path.exists(users_file_path):
        save_users({})
        print(f"Arquivo {USERS_FILE} inicializado.") # For console feedback during development

if __name__ == '__main__':
    # This part is for direct script execution testing, not directly used by Streamlit app
    initialize_users_file()
    
    # Example Usage (for testing user_management.py directly)
    # To run this: python user_management.py
    
    # Test registration
    # print("Tentando registrar 'testuser1' com senha 'password123'")
    # if register_user("testuser1", "password123"):
    #     print("Usuário 'testuser1' registrado.")
    # else:
    #     print("Falha ao registrar 'testuser1'.")

    # print("\nTentando registrar 'testuser1' novamente (deve falhar)")
    # if not register_user("testuser1", "password123"):
    #     print("Falha ao registrar 'testuser1' novamente, como esperado.")
    # else:
    #     print("Erro: 'testuser1' registrado novamente.")

    # print("\nTentando registrar 'testuser2' com senha 'securepass'")
    # if register_user("testuser2", "securepass"):
    #     print("Usuário 'testuser2' registrado.")
    # else:
    #     print("Falha ao registrar 'testuser2'.")

    # Test verification
    # print("\nVerificando 'testuser1' com senha correta 'password123'")
    # if verify_user("testuser1", "password123"):
    #     print("'testuser1' verificado com sucesso.")
    # else:
    #     print("Falha na verificação de 'testuser1'.")

    # print("\nVerificando 'testuser1' com senha incorreta 'wrongpassword'")
    # if not verify_user("testuser1", "wrongpassword"):
    #     print("Falha na verificação de 'testuser1' com senha incorreta, como esperado.")
    # else:
    #     print("Erro: 'testuser1' verificado com senha incorreta.")
        
    # print("\nVerificando usuário inexistente 'nouser'")
    # if not verify_user("nouser", "anypassword"):
    #     print("Falha na verificação de 'nouser', como esperado.")
    # else:
    #     print("Erro: 'nouser' verificado.")
    
    # print("\nConteúdo atual de users.json:")
    # print(load_users())
    pass
