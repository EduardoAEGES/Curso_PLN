@echo off
echo ========================================
echo Actualizando datos del Dashboard ClassDojo...
echo ========================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor instale Python primero: https://www.python.org/downloads/
    pause
    exit /b
)

:: Run the script
:: Using prompt for input, so the console will wait
python scraper.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el script.
    echo Revise los mensajes de arriba.
) else (
    echo.
    echo [EXITO] Datos actualizados. Abriendo dashboard...
    start dashboard.html
)

pause
