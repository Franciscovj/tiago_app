import streamlit as st
import pandas as pd

# Import functions from the main application modules
# Assuming app.py and other modules are in the parent directory
import sys
sys.path.append('..') # Add parent directory to path to import sibling modules

from state_helpers import initialize_session_state, load_all_filter_sets
from ui_controls import display_file_uploader
from filter_processing import apply_filters_to_dataframe

def run_analysis_page():
    # Page config is set in app.py
    st.title("📊 Análise de Impacto de Filtros Salvos")

    # Session state (like st.session_state.df) is shared and initialized by app.py.
    # The file uploader in the sidebar will operate on this shared st.session_state.df.
    # This means loading a file on one page makes it available on the other, which is the current design.

    # --- Sidebar for Data Upload on this specific page ---
    # Streamlit's main sidebar is used for page navigation and, on the main page, for filter set management.
    # Here, we are adding page-specific controls to that same sidebar.
    with st.sidebar: # Refers to the main Streamlit sidebar
        st.divider() # Optional: visual separator from navigation links or other sidebar items
        st.header("Carregar Dados para Análise")
        display_file_uploader(uploader_key="analysis_page_uploader") # Uses and updates st.session_state.df

    current_df = st.session_state.get('df')

    if current_df is not None and not current_df.empty:
        st.markdown("---")
        st.subheader("Selecione os Filtros Salvos para Análise")

        all_saved_filters = load_all_filter_sets()

        if not all_saved_filters:
            st.info("Nenhum conjunto de filtros salvo encontrado. Crie e salve filtros na página principal.")
            return

        filter_names = list(all_saved_filters.keys())
        selected_filter_names = st.multiselect(
            "Escolha um ou mais filtros para analisar:",
            options=filter_names,
            # default=filter_names[0] if filter_names else None # Optional: default selection
        )

        if selected_filter_names:
            st.markdown("---")
            st.subheader("Resultados da Análise")

            results_data = []
            for name in selected_filter_names:
                filter_config = all_saved_filters.get(name)
                if filter_config:
                    # Apply this specific filter set to a fresh copy of the original DataFrame
                    df_filtered_for_analysis = apply_filters_to_dataframe(current_df.copy(), filter_config)
                    line_count = len(df_filtered_for_analysis)
                    results_data.append({"Nome do Filtro": name, "Quantidade de Jogos (Linhas)": line_count})
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df, use_container_width=True)
            else:
                st.info("Nenhum filtro válido selecionado ou os filtros selecionados não puderam ser aplicados.")
        else:
            st.info("Selecione pelo menos um filtro salvo para ver a análise.")

    else:
        st.info("✨ Carregue um arquivo (XLSX, CSV, ODS) na barra lateral para começar a análise.")

if __name__ == "__main__":
    # This allows running this page standalone for testing if needed,
    # but it's primarily designed to be run via `streamlit run app.py`
    
    # Call the main function for the page
    run_analysis_page()

# To ensure that initialize_session_state() is called when app.py is the entry point
# and this page is navigated to, app.py should handle the initialization.
# If running this page standalone (python pages/02_Analise_Filtros.py), 
# then the __main__ block below would be useful.
if __name__ == "__main__":
    # This block is for testing this page in isolation.
    # In a real multi-page app, app.py initializes session state.
    print("Executando 02_Analise_Filtros.py como script principal (para teste).")
    print("Certifique-se de que 'app.py' inicializa o estado da sessão em um cenário de aplicativo de várias páginas.")
    
    # For standalone testing, we need to ensure session state is initialized.
    # This might conflict if not managed carefully with how Streamlit handles session state across reruns.
    if 'df' not in st.session_state: # Basic check
        initialize_session_state() 
        print("Estado da sessão inicializado para teste standalone.")
    
    run_analysis_page()
