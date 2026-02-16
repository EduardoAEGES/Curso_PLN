import pandas as pd

try:
    df = pd.read_excel("registro.xlsx", header=None)
    print("First 15 rows of the Excel file:")
    print(df.head(15))
    
    print("\n\nAnalyzed Row Values:")
    for i in range(min(15, len(df))):
        print(f"Row {i}: {df.iloc[i].values}")
except Exception as e:
    print(f"Error reading excel: {e}")
