import pandas as pd
import os
import time
import re
import datetime
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
EXCEL_FILE = "registro.xlsx"
CHROME_PROFILE_PATH = os.path.join(os.getcwd(), "chrome_profile")
CLASS_URL = "https://teach.classdojo.com/#/classes/697d7ed028ab93052f78c907/points" 
EMAIL = "edu.mamaniroque@gmail.com"
PASSWORD = "Conta-2025"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open("autograder_log.txt", "a", encoding="utf-8") as f:
        f.write(full_message + "\n")

def normalize_name(name):
    s = str(name).lower().strip()
    replacements = (('á','a'), ('é','e'), ('í','i'), ('ó','o'), ('ú','u'))
    for a, b in replacements:
        s = s.replace(a, b)
    return s

def get_excel_data():
    log(f"Leyendo archivo Excel: {EXCEL_FILE}...")
    try:
        log("Leyendo hoja 'Continua'...")
        df_raw = pd.read_excel(EXCEL_FILE, sheet_name="Continua", header=None)
        
        header_row_idx = -1
        col_name_idx = -1
        col_score_idx = -1
        
        for r in range(min(10, len(df_raw))):
            row_values = [str(x).strip() for x in df_raw.iloc[r].values]
            name_found = False
            score_found = False
            for c, val in enumerate(row_values):
                if "Usuario Classdojo" in val:
                    col_name_idx = c
                    name_found = True
                if "Acumulado" in val:
                    col_score_idx = c
                    score_found = True
            if name_found and score_found:
                header_row_idx = r
                break
        
        if header_row_idx == -1:
            log("Error: No se encontraron las columnas 'Usuario Classdojo' y 'Acumulado'.")
            return None

        log(f"Encabezados encontrados en fila {header_row_idx+1}.")
        student_scores = {}
        for index, row in df_raw.iloc[header_row_idx+1:].iterrows():
            name_cell = row.iloc[col_name_idx]
            score_cell = row.iloc[col_score_idx]
            if pd.isna(name_cell) or pd.isna(score_cell): continue
            name_str = str(name_cell).strip()
            try:
                score_val = float(score_cell)
                score_int = int(score_val)
            except: continue
            norm_key = normalize_name(name_str)
            student_scores[norm_key] = score_int
            
        return student_scores

    except Exception as e:
        log(f"Error leyendo Excel: {e}")
        return None

def main():
    log("=== Iniciando Autograder ClassDojo (Modo DEBUG Modal) ===")
    
    excel_scores = get_excel_data()
    if not excel_scores: return
    log(f"Objetivos cargados: {len(excel_scores)} estudiantes.")

    if not os.path.exists(CHROME_PROFILE_PATH): os.makedirs(CHROME_PROFILE_PATH)

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
    options.add_argument("--start-maximized")
    
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        log(f"Error iniciando Chrome: {e}")
        return

    try:
        log(f"Navegando a: {CLASS_URL}")
        driver.get(CLASS_URL)
        wait = WebDriverWait(driver, 30) 

        time.sleep(5)
        if "login" in driver.current_url or "welcome" in driver.current_url:
            log("Login automático...")
            try:
                email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
                email_input.clear()
                email_input.send_keys(EMAIL)
                pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                pass_input.clear()
                pass_input.send_keys(PASSWORD)
                pass_input.send_keys(Keys.RETURN)
                wait.until(EC.url_contains("classes"))
                log("Login OK.")
                driver.get(CLASS_URL) 
                time.sleep(5)
            except Exception as e:
                log(f"Fallo Login: {e}")

        log("Sincronizando puntos... (Ctrl+C para detener)")
        
        while True:
            time.sleep(2)
            buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-name='studentTile']")
            
            if not buttons:
                log("Esperando estudiantes...")
                time.sleep(2)
                continue
                
            work_done_in_this_pass = False
            
            for index, btn in enumerate(buttons):
                try:
                    aria = btn.get_attribute("aria-label")
                    if not aria: continue
                    match = re.search(r"^(.+?)\s+(-?\d+)\s+puntos?", aria, re.IGNORECASE)
                    if not match: continue
                    
                    current_name = match.group(1).strip()
                    current_points = int(match.group(2))
                    if "Dar feedback" in current_name: current_name = current_name.split("Dar feedback")[0].strip()
                        
                    norm_current = normalize_name(current_name)
                    target = excel_scores.get(norm_current)
                    
                    if target is None:
                        for k, v in excel_scores.items():
                            if k in norm_current or norm_current in k:
                                target = v
                                break
                    
                    if target is not None:
                        if current_points < target:
                            diff = target - current_points
                            log(f"[PENDIENTE] {current_name}: {current_points} -> {target} (Faltan {diff})")
                            
                            # ACTION: Add 1 point
                            driver.execute_script("arguments[0].click();", btn)
                            
                            # Wait specifically for modal
                            time.sleep(2) 
                            
                            # SAVE HTML DEBUG
                            with open("debug_modal_source.html", "w", encoding="utf-8") as f:
                                f.write(driver.page_source)
                            
                            # Find Skill to Click - Strategy: Find specific text like "Participando" or "+1"
                            # Based on screenshot, skills are buttons with text inside.
                            skill_clicked = False
                            
                            # Try 1: Text exact match "Participando"
                            try:
                                # Start with finding any element containing "Participando"
                                # Then find clickable parent
                                skill_el = driver.find_element(By.XPATH, "//div[contains(text(), 'Participando')]/ancestor::button")
                                log(f"  -> Encontrado skill 'Participando' (XPATH).")
                                driver.execute_script("arguments[0].click();", skill_el)
                                skill_clicked = True
                            except:
                                # Try 2: Any element with "+1" green bubble
                                try:
                                    # Looking for "+1" text
                                    plus_one = driver.find_element(By.XPATH, "//*[contains(text(), '+1')]/ancestor::button")
                                    log(f"  -> Encontrado skill generico '+1' (XPATH).")
                                    driver.execute_script("arguments[0].click();", plus_one)
                                    skill_clicked = True
                                except:
                                    # Try 3: Fallback list items point_weight_1
                                    try:
                                        skills = driver.find_elements(By.CSS_SELECTOR, "li[data-name='point_weight_1'] button")
                                        if skills:
                                            log(f"  -> Encontrado skill 'point_weight_1' (CSS).")
                                            driver.execute_script("arguments[0].click();", skills[0])
                                            skill_clicked = True
                                    except:
                                         pass
                            
                            if skill_clicked:
                                log(f"  -> ¡Clic realizado!")
                                work_done_in_this_pass = True
                                time.sleep(1.5)
                            else:
                                log("  -> ERROR CRÍTICO: No se pudo hacer clic en ninguna habilidad.")
                                # Close modal
                                try: driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                except: pass
                            
                            # Break inner loop to verify update
                            if skill_clicked: break 
                            else: continue

                except Exception as inner_e:
                    log(f"Error procesando {index}: {inner_e}")
                    continue
            
            if not work_done_in_this_pass:
                log("--- Sincronización COMPLETADA ---")
                break

    except Exception as e:
        log(f"Error general: {e}")
        log(traceback.format_exc())
    finally:
        log("Cerrando sesión en 5s...")
        time.sleep(5)
        if driver: driver.quit()

if __name__ == "__main__":
    main()
