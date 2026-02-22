import json
import time
import os
import re
import datetime
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "chrome_profile")
CLASS_URL = "https://teach.classdojo.com/#/classes/697d7ed028ab93052f78c907/points" 
EMAIL = "edu.mamaniroque@gmail.com"
PASSWORD = "Conta-2025"
EXCEL_URL = "https://docs.google.com/spreadsheets/d/1TaNYdspym_FSn-yY7HaAFPRxSvr2Ubmp/export?format=xlsx"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open("scraper_log.txt", "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def normalize_name(name):
    s = str(name).lower().strip()
    replacements = (('á','a'), ('é','e'), ('í','i'), ('ó','o'), ('ú','u'))
    for a, b in replacements:
        s = s.replace(a, b)
    return s

def get_excel_stats():
    """Reads Excel and returns a dict: { normalized_name: { 'participation': X, 'homework': Y, 'punctuality': Z, 'total': W } }"""
    log("Descargando y calculando estadísticas desde Google Sheets...")
    try:
        df = pd.read_excel(EXCEL_URL, sheet_name="Continua", header=None)
        
        # Find Header Row
        header_row_idx = -1
        name_col_idx = -1
        total_col_idx = -1
        
        # Identify columns indices for each category
        part_indices = []
        task_indices = []
        punct_indices = []
        
        for r in range(min(10, len(df))):
            row_vals = [str(x).strip() for x in df.iloc[r].values]
            if "Usuario Classdojo" in row_vals:
                header_row_idx = r
                for c, val in enumerate(row_vals):
                    if "Usuario Classdojo" in val: name_col_idx = c
                    elif "Acumulado" in val: total_col_idx = c
                    elif "Participación" in val: part_indices.append(c)
                    elif "Tarea" in val: task_indices.append(c)
                    elif "Puntualidad" in val: punct_indices.append(c)
                break
        
        if header_row_idx == -1:
            log("No se encontró la fila de encabezados en el Google Sheet.")
            return {}
            
        stats = {}
        
        # Process rows
        for index, row in df.iloc[header_row_idx+1:].iterrows():
            name_cell = row.iloc[name_col_idx]
            if pd.isna(name_cell): continue
            
            norm_name = normalize_name(name_cell)
            
            # Helper to sum values
            def sum_cols(indices):
                total = 0
                for c in indices:
                    try:
                        val = row.iloc[c]
                        if pd.notna(val) and str(val).strip() != "":
                            total += float(val)
                    except: pass
                return int(total)
            
            # Extract total if available
            total_points = 0
            if total_col_idx != -1:
                 val = row.iloc[total_col_idx]
                 if pd.notna(val) and str(val).strip() != "":
                     try:
                         total_points = int(float(val))
                     except: pass

            stats[norm_name] = {
                "participation": sum_cols(part_indices),
                "homework": sum_cols(task_indices),
                "punctuality": sum_cols(punct_indices),
                "total": total_points
            }
            
        log(f"Estadísticas calculadas para {len(stats)} estudiantes desde Sheets.")
        return stats

    except Exception as e:
        log(f"Error procesando el Google Sheet: {e}")
        return {}

def main():
    log("Iniciando Scraper v4.0 (Enhanced Stats)...")
    
    # 1. Get Excel Data FIRST
    excel_stats = get_excel_stats()
    
    if not os.path.exists(CHROME_PROFILE_PATH):
        os.makedirs(CHROME_PROFILE_PATH)

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
    options.add_argument("--start-maximized")
    # options.add_argument("--headless") 
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        log(f"Error CRÍTICO al iniciar Chrome: {e}")
        return

    try:
        log(f"Navegando a: {CLASS_URL}")
        driver.get(CLASS_URL)
        wait = WebDriverWait(driver, 30) 

        time.sleep(5)
        if "login" in driver.current_url or "welcome" in driver.current_url:
            log("Auto-login...")
            try:
                email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
                email_input.clear()
                email_input.send_keys(EMAIL)
                pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pass_input.clear()
                pass_input.send_keys(PASSWORD)
                pass_input.send_keys(Keys.RETURN)
                wait.until(EC.url_contains("classes"))
                log("Login OK")
                driver.get(CLASS_URL)
            except Exception as login_error:
                log(f"Error login: {login_error}")

        log("Esperando carga...")
        time.sleep(10)

        students_data = []
        student_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-name='studentTile']")
        
        log(f"Encontrados {len(student_buttons)} estudiantes.")
        
        for btn in student_buttons:
            try:
                aria_label = btn.get_attribute("aria-label")
                if not aria_label: continue
                
                match = re.search(r"^(.+?)\s+(-?\d+)\s+puntos?", aria_label, re.IGNORECASE)
                name = "Desconocido"
                points = 0
                
                if match:
                    name = match.group(1).strip()
                    points = int(match.group(2))
                else:
                    # Fallback
                    parts = aria_label.split(" punto")
                    if len(parts) > 0:
                        last_part = parts[0].split(" ")[-1]
                        if last_part.isdigit() or (last_part.startswith('-') and last_part[1:].isdigit()):
                             points = int(last_part)
                             name = parts[0].rsplit(" ", 1)[0]
                        else:
                             name = parts[0]

                if "Dar feedback" in name:
                    name = name.split("Dar feedback")[0].strip()

                if name != "Desconocido":
                    # Merge with Excel Stats
                    norm_name = normalize_name(name)
                    details = excel_stats.get(norm_name, {"participation": 0, "homework": 0, "punctuality": 0})
                    
                    # Fuzzy match fallback
                    if norm_name not in excel_stats:
                        for k, v in excel_stats.items():
                            if k in norm_name or norm_name in k:
                                details = v
                                break
                    
                    # Usa el "Acumulado" del Excel como points totales reales, en lugar del leido en classdojo
                    actual_points = details.get("total", points) if details.get("total", 0) > 0 else points
                    
                    students_data.append({
                        "name": name, 
                        "points": actual_points,
                        "details": {
                            "participation": details.get("participation", 0),
                            "homework": details.get("homework", 0),
                            "punctuality": details.get("punctuality", 0)
                        }
                    })
                    
            except Exception as e:
                log(f"Error: {e}")
                continue 

        log(f"Procesados {len(students_data)} estudiantes.")

        output_file = "data.js"
        final_data = {
            "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "students": students_data
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            students_json = json.dumps(final_data['students'], indent=4, ensure_ascii=False)
            f.write(f"window.classDojoData = {students_json};\n")
            f.write(f"window.classDojoMeta = {{ 'lastUpdated': '{final_data['timestamp']}' }};\n")
            
        log(f"Datos guardados en {output_file}")

    except Exception as e:
        log(f"Error general: {e}")
        log(traceback.format_exc())
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()
