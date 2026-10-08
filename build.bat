@echo off
chcp 65001 > nul
echo ========================================================
echo   Compilando PDF Master Suite a ejecutable (.exe)
echo   Arquitectura moderna: PySide6 (Qt) con soporte High-DPI
echo ========================================================
echo.

echo 1. Instalando / Verificando dependencias necesarias...
python -m pip install -r requirements.txt

echo.
echo 2. Iniciando compilación con PyInstaller...
python -m PyInstaller --onefile --noconsole --collect-submodules PySide6 --name "PDFMasterSuite" main.py

echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo   [EXITO] El ejecutable ha sido generado correctamente en:
    echo   dist\PDFMasterSuite.exe
) else (
    echo   [ERROR] Ocurrió un problema durante la compilación.
)
echo ========================================================
pause
