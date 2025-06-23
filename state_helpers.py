import streamlit as st
import json

SAVED_FILTERS_FILE = "named_filters.json" # Define here or pass as arg

def initialize_session_state():
    if 'filters' not in st.session_state:
        st.session_state.filters = []
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'df' not in st.session_state: 
        st.session_state.df = None
    if 'selected_sheet' not in st.session_state:
        st.session_state.selected_sheet = None
    if "filter_set_name_save_input" not in st.session_state:
        st.session_state.filter_set_name_save_input = ""
    if "selected_filter_action" not in st.session_state:
        st.session_state.selected_filter_action = "--Selecione--"

def load_all_filter_sets():
    try:
        with open(SAVED_FILTERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {} 
    except json.JSONDecodeError:
        # This function is called by ui_controls, so st.sidebar.warning is okay here.
        st.sidebar.warning(f"Arquivo '{SAVED_FILTERS_FILE}' corrompido ou vazio.")
        return {}

def save_named_filter_set(name, filters_to_save):
    if not name:
        st.sidebar.warning("Insira um nome para o conjunto de filtros.")
        return False
    if not filters_to_save:
        st.sidebar.warning("Nenhum filtro ativo para salvar.")
        return False
    
    all_sets = load_all_filter_sets()
    all_sets[name] = filters_to_save 
    try:
        with open(SAVED_FILTERS_FILE, "w") as f:
            json.dump(all_sets, f, indent=4) 
        st.sidebar.success(f"Conjunto '{name}' salvo!")
        return True
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar: {e}")
        return False

def load_named_filter_set(name):
    all_sets = load_all_filter_sets()
    if name in all_sets:
        st.session_state.filters = all_sets[name]
        st.sidebar.success(f"Conjunto '{name}' carregado!")
        st.rerun() 
    else:
        st.sidebar.error(f"Conjunto '{name}' não encontrado.")

def delete_named_filter_set(name):
    all_sets = load_all_filter_sets()
    if name in all_sets:
        del all_sets[name]
        try:
            with open(SAVED_FILTERS_FILE, "w") as f:
                json.dump(all_sets, f, indent=4)
            st.sidebar.success(f"Conjunto '{name}' excluído!")
            if st.session_state.get("selected_filter_action") == name:
                st.session_state.selected_filter_action = "--Selecione--" 
            st.rerun() 
        except Exception as e:
            st.sidebar.error(f"Erro ao excluir: {e}")
    else:
        st.sidebar.error(f"Conjunto '{name}' não encontrado.")
