import streamlit as st
import pandas as pd

# Note: SAVED_FILTERS_FILE and other constants might need to be passed or defined here too if not globally accessible
# For now, assuming they might be passed or handled by importing from a config module if this grows further.

def display_file_uploader():
    """Displays the file uploader and handles file processing.
    Updates st.session_state.df with the data from the selected sheet.
    """
    uploaded_file = st.file_uploader(
        "Escolha um arquivo XLSX", type="xlsx", key="file_uploader_widget"
    )
    if uploaded_file is not None:
        if st.session_state.uploaded_file_name != uploaded_file.name:
            st.session_state.uploaded_file_name = uploaded_file.name
            st.session_state.df = None            
            st.session_state.filters = []          
            st.session_state.selected_sheet = None 
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            current_sheet_index = 0
            if st.session_state.selected_sheet and st.session_state.selected_sheet in sheet_names:
                current_sheet_index = sheet_names.index(st.session_state.selected_sheet)
            selected_sheet_name = st.selectbox(
                "Escolha uma planilha", sheet_names, index=current_sheet_index, key="sheet_selector_widget"
            )
            if selected_sheet_name and (st.session_state.selected_sheet != selected_sheet_name or st.session_state.df is None):
                st.session_state.selected_sheet = selected_sheet_name
                st.session_state.df = pd.read_excel(xls, sheet_name=selected_sheet_name)
                st.rerun() 
        except Exception as e:
            st.error(f"Erro ao processar XLSX: {e}")
            st.session_state.uploaded_file_name = None
            st.session_state.df = None; st.session_state.filters = []; st.session_state.selected_sheet = None
    elif st.session_state.uploaded_file_name is not None: 
        st.session_state.uploaded_file_name = None
        st.session_state.df = None; st.session_state.filters = []; st.session_state.selected_sheet = None
        st.rerun()

def display_filter_controls_in_main(df_columns):
    """ Renders filter configuration controls in the main application area. """
    st.markdown("---")
    st.subheader("🔧 Configuração de Filtros")
    
    if st.button("➕ Adicionar Novo Filtro", key="add_filter_button_main_body"):
        default_col = df_columns[0] if df_columns else None
        st.session_state.filters.append({
            'type': 'column_value', 'column': default_col, 'value': None, 
            'condition': '==', 'type_display_name': "Valor da Coluna"
        })
        st.rerun()

    filters_to_remove_indices = []
    if not st.session_state.filters:
        st.info("Nenhum filtro adicionado.")

    for i, f_config in enumerate(st.session_state.filters):
        filter_type_display = f_config.get('type_display_name', 'Filtro Desconhecido')
        
        if f_config.get('type') == 'column_comparison':
            col1_name = f_config.get('column1', 'N/A')
            col2_name = f_config.get('column2', 'N/A')
            condition_symbol = f_config.get('condition', '?')
            exp_label = f"Filtro {i+1}: Comparar '{col1_name}' {condition_symbol} '{col2_name}'"
        else: # For column_value and column_range
            title_col_name = f_config.get('column', 'N/A')
            exp_label = f"Filtro {i+1}: {filter_type_display} em '{title_col_name}'"
        
        with st.expander(exp_label, expanded=True):
            r1c1, r1c2 = st.columns([0.8, 0.2])
            filter_opts = ["Valor da Coluna", "Range da Coluna", "Comparação entre Colunas"]
            curr_disp_name = f_config.get('type_display_name', filter_opts[0])
            curr_type_idx = filter_opts.index(curr_disp_name) if curr_disp_name in filter_opts else 0

            with r1c1:
                sel_disp_type = st.selectbox("Tipo de Filtro", filter_opts, index=curr_type_idx, 
                                             key=f"filter_type_main_{i}", label_visibility="collapsed")
            with r1c2:
                st.write("") 
                if st.button("🗑️ Remover", key=f"remove_btn_main_{i}", help="Remover este filtro"):
                    filters_to_remove_indices.append(i)
            
            if sel_disp_type != curr_disp_name:
                f_config['type_display_name'] = sel_disp_type
                type_map = {"Valor da Coluna": "column_value", "Range da Coluna": "column_range", "Comparação entre Colunas": "column_comparison"}
                new_type = type_map[sel_disp_type]
                
                if new_type != f_config.get('type'):
                    f_config['type'] = new_type
                    keys_to_remove = ['column', 'value', 'condition', 'column1', 'column2']
                    for key_to_remove in keys_to_remove:
                        if key_to_remove in f_config:
                            del f_config[key_to_remove]
                    
                    if new_type == 'column_value':
                        f_config.update({'column': df_columns[0] if df_columns else None, 'value': None, 'condition': '=='})
                    elif new_type == 'column_range':
                         f_config.update({'column': (df_columns[0] if df_columns and any(pd.api.types.is_numeric_dtype(st.session_state.df[c].dtype) for c in df_columns if c in st.session_state.df.columns) else None), 'value': None, 'condition': '=='})
                    elif new_type == 'column_comparison':
                        f_config.update({
                            'column1': df_columns[0] if df_columns else None,
                            'column2': df_columns[1] if len(df_columns) > 1 else (df_columns[0] if df_columns else None), 
                            'condition': '>' 
                        })
                    st.rerun()

            if f_config['type'] == 'column_value':
                cc = st.columns(3)
                with cc[0]:
                    idx = df_columns.index(f_config['column']) if f_config.get('column') in df_columns else 0
                    f_config['column'] = st.selectbox("Coluna", df_columns, index=idx, key=f"cv_col_main_{i}", label_visibility="collapsed")
                if f_config['column'] and st.session_state.df is not None:
                    dtype = st.session_state.df[f_config['column']].dtype
                    if pd.api.types.is_numeric_dtype(dtype):
                        conds = ['==', '!=', '>', '<', '>=', '<=']
                        with cc[1]:
                            c_idx = conds.index(f_config['condition']) if f_config.get('condition') in conds else 0
                            f_config['condition'] = st.selectbox("Cond.", conds, index=c_idx, key=f"cv_cond_num_main_{i}", label_visibility="collapsed")
                        with cc[2]:
                            f_config['value'] = st.number_input("Valor", value=f_config.get('value', 0.0), key=f"cv_val_num_main_{i}", label_visibility="collapsed")
                    else:
                        conds = ['==', '!=']
                        with cc[1]:
                            c_idx = conds.index(f_config['condition']) if f_config.get('condition') in conds else 0
                            f_config['condition'] = st.selectbox("Cond.", conds, index=c_idx, key=f"cv_cond_cat_main_{i}", label_visibility="collapsed")
                        with cc[2]:
                            u_vals = [''] + sorted(list(st.session_state.df[f_config['column']].astype(str).unique()))
                            s_val = str(f_config.get('value', ''))
                            v_idx = u_vals.index(s_val) if s_val in u_vals else 0
                            f_config['value'] = st.selectbox("Valor", u_vals, index=v_idx, key=f"cv_val_cat_main_{i}", label_visibility="collapsed")

            elif f_config['type'] == 'column_range':
                cr_cols = st.columns([1,2])
                with cr_cols[0]:
                    num_cols = [c for c in df_columns if st.session_state.df is not None and c in st.session_state.df.columns and pd.api.types.is_numeric_dtype(st.session_state.df[c].dtype)]
                    if not num_cols: st.warning("No num. cols."); f_config['column'] = None
                    else:
                        idx = num_cols.index(f_config['column']) if f_config.get('column') in num_cols else 0
                        f_config['column'] = st.selectbox("Col Num.", num_cols, index=idx, key=f"cr_col_main_{i}", label_visibility="collapsed")
                if f_config['column'] and st.session_state.df is not None:
                    with cr_cols[1]:
                        num_series = pd.to_numeric(st.session_state.df[f_config['column']], errors='coerce').dropna()
                        d_min, d_max = (float(num_series.min()), float(num_series.max())) if not num_series.empty else (0.0,0.1)
                        if d_min >= d_max: d_max = d_min + 0.1 
                        
                        val_f_conf = f_config.get('value')
                        init_slider_val = (d_min, d_max)
                        if isinstance(val_f_conf, (list,tuple)) and len(val_f_conf)==2 and all(isinstance(x,(int,float)) for x in val_f_conf) and val_f_conf[0]<=val_f_conf[1]:
                            disp_min = max(d_min, val_f_conf[0]); disp_max = min(d_max, val_f_conf[1])
                            init_slider_val = (disp_min, disp_max) if disp_min <= disp_max else (d_min, d_max)
                        
                        slider_out = st.slider(f"Intervalo '{f_config['column']}'", min_value=d_min, max_value=d_max, value=init_slider_val, key=f"cr_slider_main_{i}", label_visibility="collapsed")
                        if f_config.get('value') != list(slider_out): f_config['value'] = list(slider_out)

            elif f_config['type'] == 'column_comparison':
                comp_cols = st.columns(3)
                with comp_cols[0]:
                    idx1 = df_columns.index(f_config['column1']) if f_config.get('column1') in df_columns else 0
                    f_config['column1'] = st.selectbox("Coluna 1", df_columns, index=idx1, key=f"cc_col1_main_{i}", label_visibility="collapsed")
                with comp_cols[1]:
                    conds = ['>', '<', '>=', '<=', '==', '!=']
                    c_idx = conds.index(f_config['condition']) if f_config.get('condition') in conds else 0
                    f_config['condition'] = st.selectbox("Cond.", conds, index=c_idx, key=f"cc_cond_main_{i}", label_visibility="collapsed")
                with comp_cols[2]:
                    idx2 = df_columns.index(f_config['column2']) if f_config.get('column2') in df_columns else 0
                    f_config['column2'] = st.selectbox("Coluna 2", df_columns, index=idx2, key=f"cc_col2_main_{i}", label_visibility="collapsed")

    if filters_to_remove_indices:
        for index in sorted(filters_to_remove_indices, reverse=True):
            st.session_state.filters.pop(index)
        st.rerun()

# This function depends on load_all_filter_sets, save_named_filter_set, 
# load_named_filter_set, delete_named_filter_set which should be in state_helpers.py
# For now, keep it here and adjust imports later if state_helpers.py is created.
# Or, pass these functions as arguments if ui_controls is to be fully independent.
# For simplicity of this step, we'll assume state helper functions are accessible.
# If state_helpers.py is created, these would be: from state_helpers import ...

# To avoid circular dependency if state_helpers needs SAVED_FILTERS_FILE:
# It's better if SAVED_FILTERS_FILE is defined in a config or passed around.
# For now, assume state_helpers can access it or it's passed to them.

# Importing helper functions from state_helpers
# This assumes state_helpers.py is in the same directory or accessible via PYTHONPATH
from state_helpers import (
    load_all_filter_sets,
    save_named_filter_set,
    load_named_filter_set,
    delete_named_filter_set
)

def display_save_load_filter_sets_controls():
    st.sidebar.subheader("Salvar Filtros Atuais")
    filter_set_name_save_widget = st.sidebar.text_input(
        "Nome para o conjunto", value=st.session_state.get("filter_set_name_save_input", ""),
        key="filter_set_name_save_input_widget"
    )
    st.session_state.filter_set_name_save_input = filter_set_name_save_widget
    if st.sidebar.button("Salvar Conjunto", key="save_filter_set_btn"):
        name_to_save = st.session_state.filter_set_name_save_input
        # Now calls the imported function directly
        if save_named_filter_set(name_to_save, st.session_state.filters): 
            st.session_state.filter_set_name_save_input = ""; st.rerun()

    st.sidebar.subheader("Carregar ou Excluir Salvos")
    saved_sets = load_all_filter_sets() # Call imported function
    if saved_sets:
        names = ["--Selecione--"] + sorted(list(saved_sets.keys()))
        sel_set_name = st.sidebar.selectbox("Conjuntos salvos", names, key="selected_filter_action")
        if sel_set_name != "--Selecione--":
            sb_c1, sb_c2 = st.sidebar.columns(2)
            with sb_c1:
                if st.button("Carregar", key="load_sel_filt_btn", help="Carregar"): 
                    load_named_filter_set(sel_set_name) # Call imported function
            with sb_c2:
                if st.button("Excluir", key="del_sel_filt_btn", help="Excluir"): 
                    delete_named_filter_set(sel_set_name) # Call imported function
    else: st.sidebar.info("Nenhum conjunto salvo.")

# The check `if c in st.session_state.df.columns` was added in list comp for `column_range` `f_config.update`
# to prevent KeyError if df_columns[0] isn't actually numeric.
# Also, for `column_range` `num_cols` list comprehension, added `c in st.session_state.df.columns`
# to prevent errors if a column name from df_columns is no longer in the actual df (e.g. after sheet change if not reset).
