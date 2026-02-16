@echo off
echo ========================================
echo Instalando librerias necesarias (Selenium)...
echo ========================================

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor instale Python primero: https://www.python.org/downloads/
    pause
    exit /b
)

:: Install libraries
pip install selenium webdriver-manager pandas openpyxl

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al instalar las librerias.
    echo Asegurese de tener acceso a internet y permisos.
    pause
) else (
    echo.
    echo [EXITO] Librerias instaladas correctamente.
    echo Ahora puede ejecutar ACTUALIZAR_NOTAS.bat
    pause
)
