import pandas as pd

try:
    xl = pd.ExcelFile("registro.xlsx")
    print("Sheet names:", xl.sheet_names)
    
    # Try to find the right sheet
    target_sheet = None
    for sheet in xl.sheet_names:
        print(f"\n--- Checking sheet: {sheet} ---")
        df = pd.read_excel("registro.xlsx", sheet_name=sheet, header=None, nrows=10)
        print(df.head(5))
        
        # Check for our keywords
        found = False
        for r in range(len(df)):
            row_str = str(df.iloc[r].values)
            if "Classdojo" in row_str or "Acumulado" in row_str:
                print(f"FOUND MATCHING COLUMNS IN SHEET: {sheet}")
                found = True
                break
        if found:
            target_sheet = sheet
            break
            
except Exception as e:
    print(f"Error: {e}")
