import pandas as pd
import os

EXCEL_FILE = "registro.xlsx"

def normalize_name(name):
    s = str(name).lower().strip()
    replacements = (('á','a'), ('é','e'), ('í','i'), ('ó','o'), ('ú','u'))
    for a, b in replacements:
        s = s.replace(a, b)
    return s

def get_excel_stats():
    print("Calculando estadísticas desde Excel...")
    try:
        if not os.path.exists(EXCEL_FILE):
            print("ADVERTENCIA: No se encontró registro.xlsx")
            return {}

        df = pd.read_excel(EXCEL_FILE, sheet_name="Continua", header=None)
        
        header_row_idx = -1
        name_col_idx = -1
        
        part_indices = []
        task_indices = []
        punct_indices = []
        
        for r in range(min(10, len(df))):
            row_vals = [str(x).strip() for x in df.iloc[r].values]
            if "Usuario Classdojo" in row_vals:
                header_row_idx = r
                for c, val in enumerate(row_vals):
                    if "Usuario Classdojo" in val: name_col_idx = c
                    elif "Participación" in val: part_indices.append(c)
                    elif "Tarea" in val: task_indices.append(c)
                    elif "Puntualidad" in val: punct_indices.append(c)
                break
        
        if header_row_idx == -1:
            print("No se encontró la fila de encabezados en Excel.")
            return {}
            
        stats = {}
        
        for index, row in df.iloc[header_row_idx+1:].iterrows():
            name_cell = row.iloc[name_col_idx]
            if pd.isna(name_cell): continue
            
            norm_name = normalize_name(name_cell)
            if "nan" == norm_name: continue

            def sum_cols(indices):
                total = 0
                for c in indices:
                    try:
                        val = row.iloc[c]
                        if pd.notna(val):
                            total += float(val)
                    except: pass
                return int(total)

            stats[norm_name] = {
                "participation": sum_cols(part_indices),
                "homework": sum_cols(task_indices),
                "punctuality": sum_cols(punct_indices)
            }
            
        print(f"Estadísticas calculadas para {len(stats)} estudiantes.")
        # Print sample
        if stats:
             first_key = list(stats.keys())[0]
             print(f"Muestra ({first_key}): {stats[first_key]}")
        return stats

    except Exception as e:
        print(f"Error procesando Excel: {e}")
        return {}

if __name__ == "__main__":
    get_excel_stats()
