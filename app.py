import streamlit as st
import pandas as pd # Keep pandas for DataFrame checks if any remain in main, or for type hints

# Import functions from the new modules
from state_helpers import initialize_session_state
from ui_controls import (
    display_file_uploader, 
    display_filter_controls_in_main, 
    display_save_load_filter_sets_controls
)
from filter_processing import apply_filters_to_dataframe
st.set_page_config(layout="wide") 
APP_TITLE = "Filtro Dinâmico e Análise de XLSX" # Global constant

# --- Main Application Logic ---
def main():
    st.title(APP_TITLE)
    initialize_session_state() # From state_helpers

    # --- Sidebar for Save/Load Operations ---
    # Title for this section is now part of display_save_load_filter_sets_controls
    # or can be added here if preferred.
    # For now, let the function handle its own subheaders.
    # with st.sidebar:
    # st.markdown("## 💾 Gerenciar Filtros") 

    # --- Main Panel ---
    display_file_uploader() # From ui_controls
    
    current_df = st.session_state.get('df')

    if current_df is not None and not current_df.empty:
        active_filters = st.session_state.get('filters', [])
        df_filtered = apply_filters_to_dataframe(current_df, active_filters) # From filter_processing

        st.subheader("📊 Visualização dos Dados")
        st.dataframe(df_filtered, height=300) 
        st.markdown(f"**Resumo:** Original: `{len(current_df)}` linhas | Filtrado: `{len(df_filtered)}` linhas")

        # Filter configuration section moved to main body
        display_filter_controls_in_main(list(current_df.columns)) # From ui_controls

        if active_filters: # Display active filters (JSON)
            with st.expander("Ver Definição JSON dos Filtros Ativos", expanded=False):
                st.json(active_filters) 
        
        # display_save_load_filter_sets_controls is now called here, ensuring df exists
        # It internally uses st.sidebar.
        display_save_load_filter_sets_controls() # From ui_controls
            
    else:
        st.info("✨ Bem-vindo! Carregue um arquivo XLSX para começar.")

if __name__ == "__main__":
    main()
