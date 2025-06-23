import pandas as pd
import streamlit as st # For st.warning/st.error, consider using a logger for better separation

def apply_filters_to_dataframe(original_df, active_filters):
    if not active_filters or original_df is None or original_df.empty:
        return original_df if original_df is not None else pd.DataFrame()
    
    df_filtered = original_df.copy()

    for i, f_config in enumerate(active_filters):
        try:
            filter_type = f_config.get('type')
            col = f_config.get('column') # Used by column_value and column_range

            if filter_type == 'column_value':
                cond, val = f_config.get('condition'), f_config.get('value')
                if not col or val is None or (isinstance(val, str) and val == ''):
                    continue
                
                target_dtype = original_df[col].dtype
                try: 
                    if pd.api.types.is_numeric_dtype(target_dtype):
                        val = pd.to_numeric(val)
                except ValueError:
                    st.warning(f"Filtro {i+1} ({col}): Valor '{val}' incompatível com tipo numérico da coluna. Filtro ignorado.")
                    continue
                
                if cond == '==': df_filtered = df_filtered[df_filtered[col] == val]
                elif cond == '!=': df_filtered = df_filtered[df_filtered[col] != val]
                elif pd.api.types.is_numeric_dtype(target_dtype): 
                    if cond == '>': df_filtered = df_filtered[df_filtered[col] > val]
                    elif cond == '<': df_filtered = df_filtered[df_filtered[col] < val]
                    elif cond == '>=': df_filtered = df_filtered[df_filtered[col] >= val]
                    elif cond == '<=': df_filtered = df_filtered[df_filtered[col] <= val]
                elif cond in ['>', '<', '>=', '<=']: 
                    st.warning(f"Filtro {i+1} ({col}): Operação '{cond}' não aplicável a coluna não numérica. Filtro ignorado.")
                    continue

            elif filter_type == 'column_range':
                rng_val = f_config.get('value')
                if not col or not rng_val or not (isinstance(rng_val, (list,tuple)) and len(rng_val)==2):
                    continue
                min_v, max_v = rng_val[0], rng_val[1]
                num_series = pd.to_numeric(df_filtered[col], errors='coerce')
                df_filtered = df_filtered[num_series.notna() & (num_series >= min_v) & (num_series <= max_v)]

            elif filter_type == 'column_comparison':
                c1, cnd, c2 = f_config.get('column1'), f_config.get('condition'), f_config.get('column2')
                if not c1 or not c2: continue

                s1_numeric = pd.to_numeric(df_filtered[c1], errors='coerce')
                s2_numeric = pd.to_numeric(df_filtered[c2], errors='coerce')
                valid_comparison_mask = s1_numeric.notna() & s2_numeric.notna()
                
                if not valid_comparison_mask.any(): 
                    df_filtered = df_filtered.iloc[0:0] 
                    continue

                comparable_s1 = s1_numeric[valid_comparison_mask]
                comparable_s2 = s2_numeric[valid_comparison_mask]
                
                if cnd == '>': result_mask = comparable_s1 > comparable_s2
                elif cnd == '<': result_mask = comparable_s1 < comparable_s2
                elif cnd == '>=': result_mask = comparable_s1 >= comparable_s2
                elif cnd == '<=': result_mask = comparable_s1 <= comparable_s2
                elif cnd == '==': result_mask = comparable_s1 == comparable_s2
                elif cnd == '!=': result_mask = comparable_s1 != comparable_s2
                else: 
                    result_mask = pd.Series([False] * len(comparable_s1), index=comparable_s1.index)
                
                comparable_df_slice = df_filtered[valid_comparison_mask]
                df_filtered = comparable_df_slice[result_mask]
        
        except Exception as e: 
            # It's generally better to log errors or display a generic message in UI
            # st.error might be too intrusive if many filters cause minor issues.
            st.error(f"Erro ao aplicar filtro {i+1} (Tipo: {f_config.get('type')}, Col: {col or f_config.get('column1')}): {e}")
            continue 
            
    return df_filtered
