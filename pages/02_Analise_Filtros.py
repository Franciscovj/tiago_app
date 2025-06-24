import streamlit as st
import pandas as pd
import sys

# Add parent directory to path to import sibling modules
sys.path.append('..') 

from state_helpers import load_all_filter_sets 
from ui_controls import display_file_uploader
from filter_processing import apply_filters_to_dataframe

def run_analysis_page():
    st.title("📊 Análise de Impacto de Filtros Salvos")

    # Session state (df, filters, etc.) is initialized by app.py and shared.
    # File uploader for this page, with a unique key.
    with st.sidebar:
        st.divider() 
        st.header("Carregar Dados para Análise")
        # Ensure this key is DIFFERENT from the default key used in app.py
        display_file_uploader(uploader_key="analysis_page_uploader") 

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
        )

        if selected_filter_names:
            st.markdown("---")
            st.subheader("Resultados da Análise")

            results_data = []
            # Use a fresh copy of the original DataFrame for each filter analysis
            df_for_analysis = current_df.copy() 

            for name in selected_filter_names:
                filter_config = all_saved_filters.get(name)
                if filter_config:
                    # Apply this specific filter set
                    df_filtered_for_this_analysis = apply_filters_to_dataframe(df_for_analysis, filter_config)
                    line_count = len(df_filtered_for_this_analysis)
                    results_data.append({"Nome do Filtro": name, "Quantidade de Jogos (Linhas)": line_count})
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df, use_container_width=True)
            else:
                # This case might occur if selected_filter_names is not empty but all_saved_filters.get(name) fails for all.
                st.info("Não foi possível aplicar os filtros selecionados ou os filtros não produziram resultados.")
        elif all_saved_filters : # Only show this if there are filters to select from but none were selected
            st.info("Selecione pelo menos um filtro salvo para ver a análise.")
        # If no saved filters at all, the earlier message "Nenhum conjunto de filtros..." is shown.

    else:
        st.info("✨ Carregue um arquivo (XLSX, CSV, ODS) na barra lateral para começar a análise.")

# This ensures the page's content is rendered when Streamlit navigates to it.
run_analysis_page()
