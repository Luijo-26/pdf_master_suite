@echo off
chcp 65001 > nul
echo ========================================================
echo   Compilando PDF Master Suite a ejecutable (.exe)
echo ========================================================
echo.
echo 1. Verificando dependencias...
python -m pip install -r requirements.txt
echo.
echo 2. Compilando con PyInstaller...
python -m PyInstaller --onefile --noconsole --hidden-import PySide6.QtPdf --hidden-import PySide6.QtSvg --name PDFMasterSuite main.py
echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo   [EXITO] Ejecutable generado en dist\PDFMasterSuite.exe
) else (
    echo   [ERROR] Fallo la compilacion.
)
echo ========================================================
pause
