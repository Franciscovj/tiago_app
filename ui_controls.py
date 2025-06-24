import streamlit as st
import pandas as pd

from state_helpers import (
    load_all_filter_sets,
    save_named_filter_set,
    load_named_filter_set,
    delete_named_filter_set
)

def display_file_uploader(uploader_key: str = "default_file_uploader_widget"):
    """Displays the file uploader and handles file processing for XLSX, CSV, and ODS.
    Updates st.session_state.df with the data from the selected file/sheet.

    Args:
        uploader_key (str, optional): A unique key for the file uploader widget. 
                                      Defaults to "default_file_uploader_widget".
    """
    # Ensure session state for uploader is initialized if not present
    # This is particularly important for new_file_uploaded logic
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'selected_sheet' not in st.session_state:
        st.session_state.selected_sheet = None
    # 'df' and 'filters' should be initialized by initialize_session_state() in app.py

    uploaded_file = st.file_uploader(
        "Escolha um arquivo (XLSX, CSV, ODS)", 
        type=["xlsx", "csv", "ods"], 
        key=uploader_key
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Check if it's a new file OR if the uploader key itself has changed (e.g. different page context)
        # This check might be too simplistic if keys are reused in complex ways, but for two distinct keys it should be fine.
        # The core idea is, if the file object itself is new, or its name is new, reset.
        if st.session_state.get(f"{uploader_key}_processed_file_name") != uploaded_file.name:
            st.session_state.uploaded_file_name = uploaded_file.name # Shared state for file name
            st.session_state.df = None            # Shared DataFrame
            st.session_state.filters = []          # Shared active filters
            st.session_state.selected_sheet = None # Shared sheet selection
            st.session_state[f"{uploader_key}_processed_file_name"] = uploaded_file.name # Mark this uploader instance has processed this file name

        try:
            df_to_load = None
            sheet_selection_key_base = f"{uploader_key}_sheet_selector"

            if file_extension == "xlsx":
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                
                if len(sheet_names) > 1:
                    current_sheet_index = 0
                    # Use a more specific session state key for the selected sheet if needed, e.g., tied to uploader_key
                    # For now, st.session_state.selected_sheet is global.
                    if st.session_state.selected_sheet and st.session_state.selected_sheet in sheet_names:
                        current_sheet_index = sheet_names.index(st.session_state.selected_sheet)
                    
                    selected_sheet_name_key = f"{sheet_selection_key_base}_xlsx"
                    selected_sheet_name = st.selectbox(
                        "Escolha uma planilha (XLSX)", 
                        sheet_names, 
                        index=current_sheet_index, 
                        key=selected_sheet_name_key
                    )
                else:
                    selected_sheet_name = sheet_names[0]

                if st.session_state.selected_sheet != selected_sheet_name or st.session_state.df is None:
                    st.session_state.selected_sheet = selected_sheet_name
                    df_to_load = pd.read_excel(xls, sheet_name=selected_sheet_name)

            elif file_extension == "ods":
                xls = pd.ExcelFile(uploaded_file, engine='odf')
                sheet_names = xls.sheet_names

                if len(sheet_names) > 1:
                    current_sheet_index = 0
                    if st.session_state.selected_sheet and st.session_state.selected_sheet in sheet_names:
                        current_sheet_index = sheet_names.index(st.session_state.selected_sheet)
                    
                    selected_sheet_name_key = f"{sheet_selection_key_base}_ods"
                    selected_sheet_name = st.selectbox(
                        "Escolha uma planilha (ODS)", 
                        sheet_names, 
                        index=current_sheet_index, 
                        key=selected_sheet_name_key
                    )
                else:
                    selected_sheet_name = sheet_names[0]
                
                if st.session_state.selected_sheet != selected_sheet_name or st.session_state.df is None:
                    st.session_state.selected_sheet = selected_sheet_name
                    df_to_load = pd.read_excel(xls, sheet_name=selected_sheet_name, engine='odf')
            
            elif file_extension == "csv":
                st.session_state.selected_sheet = None 
                if st.session_state.df is None or st.session_state.uploaded_file_name != uploaded_file.name : # simplified condition for CSV
                    df_to_load = pd.read_csv(uploaded_file)
            
            if df_to_load is not None:
                st.session_state.df = df_to_load
                # Reset filters when a new DataFrame is loaded to avoid applying old filters to new data structure
                st.session_state.filters = [] 
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar o arquivo ({uploaded_file.name}): {e}")
            st.session_state.uploaded_file_name = None
            st.session_state.df = None
            st.session_state.filters = []
            st.session_state.selected_sheet = None
            st.session_state.pop(f"{uploader_key}_processed_file_name", None) # Clear processed file marker
            st.rerun()

    elif st.session_state.uploaded_file_name is not None and uploaded_file is None: 
        # This condition means a file was previously uploaded but now the uploader is empty (user removed it)
        st.session_state.uploaded_file_name = None
        st.session_state.df = None
        st.session_state.filters = []
        st.session_state.selected_sheet = None
        st.session_state.pop(f"{uploader_key}_processed_file_name", None) # Clear processed file marker
        st.rerun()


def display_filter_controls_in_main(df_columns):
    """ Renders filter configuration controls in the main application area. """
    st.markdown("---")
    st.subheader("🔧 Configuração de Filtros")
    
    if not df_columns: # Handle case where df_columns might be empty
        st.warning("Não há colunas disponíveis para configurar filtros. Carregue um arquivo com colunas.")
        return

    if st.button("➕ Adicionar Novo Filtro", key="add_filter_button_main_body"):
        default_col = df_columns[0] if df_columns else None
        st.session_state.filters.append({
            'type': 'column_value', 'column': default_col, 'value': None, 
            'condition': '==', 'type_display_name': "Valor da Coluna"
        })
        st.rerun()

    filters_to_remove_indices = []
    if not st.session_state.get('filters', []): # Use .get for safety
        st.info("Nenhum filtro adicionado.")
        return # No need to iterate if no filters

    for i, f_config in enumerate(st.session_state.filters):
        filter_type_display = f_config.get('type_display_name', 'Filtro Desconhecido')
        
        # Construct expander label
        exp_label_parts = [f"Filtro {i+1}"]
        if f_config.get('type') == 'column_comparison':
            col1_name = f_config.get('column1', 'N/A')
            col2_name = f_config.get('column2', 'N/A')
            condition_symbol = f_config.get('condition', '?')
            exp_label_parts.extend([": Comparar", f"'{col1_name}'", condition_symbol, f"'{col2_name}'"])
        else:
            title_col_name = f_config.get('column', 'N/A')
            exp_label_parts.extend([f": {filter_type_display} em", f"'{title_col_name}'"])
        exp_label = " ".join(exp_label_parts)

        with st.expander(exp_label, expanded=True):
            r1c1, r1c2 = st.columns([0.8, 0.2])
            filter_opts = ["Valor da Coluna", "Range da Coluna", "Comparação entre Colunas"]
            # Ensure f_config has 'type_display_name' or default safely
            curr_disp_name = f_config.get('type_display_name', filter_opts[0])
            try:
                curr_type_idx = filter_opts.index(curr_disp_name)
            except ValueError:
                curr_type_idx = 0 # Default to first option if name is somehow invalid

            with r1c1:
                sel_disp_type = st.selectbox("Tipo de Filtro", filter_opts, index=curr_type_idx, 
                                             key=f"filter_type_main_{i}", label_visibility="collapsed")
            with r1c2:
                # st.write("") # No longer needed for spacing with label_visibility
                if st.button("🗑️ Remover", key=f"remove_btn_main_{i}", help="Remover este filtro"):
                    filters_to_remove_indices.append(i)
            
            if sel_disp_type != curr_disp_name:
                f_config['type_display_name'] = sel_disp_type
                type_map = {"Valor da Coluna": "column_value", "Range da Coluna": "column_range", "Comparação entre Colunas": "column_comparison"}
                new_type = type_map[sel_disp_type]
                
                if new_type != f_config.get('type'):
                    f_config['type'] = new_type
                    # Clear out old keys more carefully
                    keys_to_clear_for_new_type = ['column', 'value', 'condition', 'column1', 'column2']
                    for key_to_remove in keys_to_clear_for_new_type:
                        f_config.pop(key_to_remove, None) # Use pop with default to avoid KeyError
                    
                    # Initialize with new defaults
                    if new_type == 'column_value':
                        f_config.update({'column': df_columns[0] if df_columns else None, 'value': '', 'condition': '=='})
                    elif new_type == 'column_range':
                         f_config.update({'column': (df_columns[0] if df_columns and st.session_state.df is not None and any(pd.api.types.is_numeric_dtype(st.session_state.df[c].dtype) for c in df_columns if c in st.session_state.df.columns) else None), 
                                          'value': [0,0], 'condition': '=='}) # Default range e.g. [min, max] from data later
                    elif new_type == 'column_comparison':
                        f_config.update({
                            'column1': df_columns[0] if df_columns else None,
                            'column2': df_columns[1] if len(df_columns) > 1 else (df_columns[0] if df_columns else None), 
                            'condition': '>' 
                        })
                    st.rerun()

            # Ensure st.session_state.df exists before trying to access its columns or dtypes
            if st.session_state.get('df') is None:
                st.warning("DataFrame não carregado. Por favor, carregue um arquivo.")
                continue # Skip rendering this filter's controls if df is not available

            if f_config['type'] == 'column_value':
                cc_val = st.columns(3)
                current_col_val = f_config.get('column', df_columns[0] if df_columns else None)
                try:
                    idx_val = df_columns.index(current_col_val) if current_col_val in df_columns else 0
                except ValueError: # Should not happen if df_columns is current
                    idx_val = 0
                
                with cc_val[0]:
                    f_config['column'] = st.selectbox("Coluna", df_columns, index=idx_val, key=f"cv_col_val_{i}", label_visibility="collapsed")
                
                if f_config['column'] and f_config['column'] in st.session_state.df.columns:
                    dtype = st.session_state.df[f_config['column']].dtype
                    if pd.api.types.is_numeric_dtype(dtype):
                        conds = ['==', '!=', '>', '<', '>=', '<=']
                        with cc_val[1]:
                            c_idx = conds.index(f_config.get('condition','==')) if f_config.get('condition','==') in conds else 0
                            f_config['condition'] = st.selectbox("Cond.", conds, index=c_idx, key=f"cv_cond_num_val_{i}", label_visibility="collapsed")
                        with cc_val[2]:
                            # Ensure 'value' exists in f_config before trying to use it, default to 0.0 for numeric
                            val_num = f_config.get('value', 0.0)
                            try: # Try to convert to float if it's not already, for number_input
                                val_num = float(val_num) if not isinstance(val_num, (int, float)) else val_num
                            except ValueError:
                                val_num = 0.0 # Default if conversion fails
                            f_config['value'] = st.number_input("Valor", value=val_num, key=f"cv_val_num_val_{i}", label_visibility="collapsed", format="%g")
                    else: # Categorical / Text
                        conds = ['==', '!=']
                        with cc_val[1]:
                            c_idx = conds.index(f_config.get('condition','==')) if f_config.get('condition','==') in conds else 0
                            f_config['condition'] = st.selectbox("Cond.", conds, index=c_idx, key=f"cv_cond_cat_val_{i}", label_visibility="collapsed")
                        with cc_val[2]:
                            u_vals = [''] + sorted(list(st.session_state.df[f_config['column']].astype(str).unique()))
                            s_val = str(f_config.get('value', ''))
                            v_idx = u_vals.index(s_val) if s_val in u_vals else 0
                            f_config['value'] = st.selectbox("Valor", u_vals, index=v_idx, key=f"cv_val_cat_val_{i}", label_visibility="collapsed")
                else:
                     with cc_val[1]: st.empty() # Keep layout consistent
                     with cc_val[2]: st.empty()


            elif f_config['type'] == 'column_range':
                cr_cols_rng = st.columns([1,2])
                num_cols = [c for c in df_columns if c in st.session_state.df.columns and pd.api.types.is_numeric_dtype(st.session_state.df[c].dtype)]
                
                current_col_rng = f_config.get('column')
                if not num_cols: 
                    with cr_cols_rng[0]: st.warning("Nenhuma coluna numérica disponível."); f_config['column'] = None
                    with cr_cols_rng[1]: st.empty()
                else:
                    try:
                        idx_rng = num_cols.index(current_col_rng) if current_col_rng in num_cols else 0
                    except ValueError: # current_col_rng might not be in num_cols if df changed
                        idx_rng = 0
                    
                    with cr_cols_rng[0]:
                        f_config['column'] = st.selectbox("Coluna Num.", num_cols, index=idx_rng, key=f"cr_col_rng_{i}", label_visibility="collapsed")
                    
                    if f_config['column'] and f_config['column'] in st.session_state.df.columns: # Ensure column still exists
                        with cr_cols_rng[1]:
                            num_series = pd.to_numeric(st.session_state.df[f_config['column']], errors='coerce').dropna()
                            d_min, d_max = (float(num_series.min()), float(num_series.max())) if not num_series.empty else (0.0, 0.1)
                            if d_min >= d_max: d_max = d_min + (0.1 if d_min == 0 else abs(d_min * 0.1) or 0.1) # Ensure max > min
                            
                            # Ensure 'value' for range is a list of two numbers
                            val_f_conf = f_config.get('value', [d_min, d_max])
                            if not (isinstance(val_f_conf, (list,tuple)) and len(val_f_conf)==2 and all(isinstance(x,(int,float)) for x in val_f_conf)):
                                val_f_conf = [d_min, d_max] # Default to full range if invalid
                            
                            # Clamp initial slider values to be within actual data min/max
                            init_slider_min = max(d_min, float(val_f_conf[0]))
                            init_slider_max = min(d_max, float(val_f_conf[1]))
                            if init_slider_min > init_slider_max : # Ensure min <= max
                                init_slider_min, init_slider_max = d_min, d_max


                            slider_out = st.slider(f"Intervalo para '{f_config['column']}'", 
                                                   min_value=d_min, max_value=d_max, 
                                                   value=(init_slider_min, init_slider_max), 
                                                   key=f"cr_slider_rng_{i}", label_visibility="collapsed")
                            if f_config.get('value') != list(slider_out): f_config['value'] = list(slider_out)
                    else: # Column not valid for range slider
                        with cr_cols_rng[1]: st.empty()


            elif f_config['type'] == 'column_comparison':
                comp_cols_cmp = st.columns(3)
                # Coluna 1
                current_col1_cmp = f_config.get('column1', df_columns[0] if df_columns else None)
                try:
                    idx1_cmp = df_columns.index(current_col1_cmp) if current_col1_cmp in df_columns else 0
                except ValueError: idx1_cmp = 0
                with comp_cols_cmp[0]:
                    f_config['column1'] = st.selectbox("Coluna 1", df_columns, index=idx1_cmp, key=f"cc_col1_cmp_{i}", label_visibility="collapsed")
                
                # Condição
                with comp_cols_cmp[1]:
                    conds_cmp = ['>', '<', '>=', '<=', '==', '!=']
                    current_cond_cmp = f_config.get('condition', '>')
                    c_idx_cmp = conds_cmp.index(current_cond_cmp) if current_cond_cmp in conds_cmp else 0
                    f_config['condition'] = st.selectbox("Cond.", conds_cmp, index=c_idx_cmp, key=f"cc_cond_cmp_{i}", label_visibility="collapsed")
                
                # Coluna 2
                current_col2_cmp = f_config.get('column2', df_columns[1] if len(df_columns) > 1 else (df_columns[0] if df_columns else None))
                try:
                    idx2_cmp = df_columns.index(current_col2_cmp) if current_col2_cmp in df_columns else (0 if not df_columns or len(df_columns) == 1 else 1)
                except ValueError: idx2_cmp = (0 if not df_columns or len(df_columns) == 1 else 1)

                with comp_cols_cmp[2]:
                    f_config['column2'] = st.selectbox("Coluna 2", df_columns, index=idx2_cmp, key=f"cc_col2_cmp_{i}", label_visibility="collapsed")

    if filters_to_remove_indices:
        for index in sorted(filters_to_remove_indices, reverse=True):
            st.session_state.filters.pop(index)
        st.rerun()

def display_save_load_filter_sets_controls():
    # This function is designed to be called within a `with st.sidebar:` block or similar context
    st.subheader("Salvar Filtros Atuais")
    filter_set_name_save_widget = st.text_input( # Changed from st.sidebar.text_input
        "Nome para o conjunto", value=st.session_state.get("filter_set_name_save_input", ""),
        key="filter_set_name_save_input_widget"
    )
    st.session_state.filter_set_name_save_input = filter_set_name_save_widget
    if st.button("Salvar Conjunto", key="save_filter_set_btn"): # Changed from st.sidebar.button
        name_to_save = st.session_state.filter_set_name_save_input
        if save_named_filter_set(name_to_save, st.session_state.get('filters',[])): # Pass active filters
            st.session_state.filter_set_name_save_input = ""
            st.rerun()

    st.subheader("Carregar ou Excluir Salvos") # Changed from st.sidebar.subheader
    saved_sets = load_all_filter_sets() 
    if saved_sets:
        names = ["--Selecione--"] + sorted(list(saved_sets.keys()))
        # Ensure selected_filter_action is initialized
        current_selection = st.session_state.get("selected_filter_action", "--Selecione--")
        if current_selection not in names: # If current selection is no longer valid (e.g. deleted)
             current_selection = "--Selecione--"
        
        sel_set_name = st.selectbox("Conjuntos salvos", names, index=names.index(current_selection), key="selected_filter_action_dropdown") # Changed key and widget

        if sel_set_name != "--Selecione--":
            # Use columns within the current context (sidebar or main)
            sb_c1, sb_c2 = st.columns(2) 
            with sb_c1:
                if st.button("Carregar", key="load_sel_filt_btn_new", help="Carregar conjunto selecionado"): 
                    load_named_filter_set(sel_set_name) 
            with sb_c2:
                if st.button("Excluir", key="del_sel_filt_btn_new", help="Excluir conjunto selecionado", type="primary"): 
                    delete_named_filter_set(sel_set_name)
                    st.session_state.selected_filter_action_dropdown = "--Selecione--" # Reset dropdown
                    st.rerun() # Rerun to reflect deletion
    else: 
        st.info("Nenhum conjunto salvo.") # Changed from st.sidebar.info

# The check `if c in st.session_state.df.columns` was added in list comp for `column_range` `f_config.update`
# to prevent KeyError if df_columns[0] isn't actually numeric.
# Also, for `column_range` `num_cols` list comprehension, added `c in st.session_state.df.columns`
# to prevent errors if a column name from df_columns is no longer in the actual df (e.g. after sheet change if not reset).
