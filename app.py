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
initialize_session_state() 

APP_TITLE = "Filtro Dinâmico e Análise de Arquivos"

# Page Configuration - should be the first Streamlit command after state init
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded" 
)

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
    main_page()
