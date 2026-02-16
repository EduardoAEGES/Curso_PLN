@echo off
echo ========================================
echo ASIGNADOR DE PUNTOS CLASSDOJO (Excel)
echo ========================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado.
    pause
    exit /b
)

echo Leyendo registro.xlsx y sincronizando con ClassDojo...
echo No cierres esta ventana.
echo Para detener el proceso presiona Ctrl+C.
echo.

python autograder.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar el script.
    echo Revisa autograder_log.txt para más detalles.
) else (
    echo.
    echo [EXITO] Sincronización finalizada.
)

pause
