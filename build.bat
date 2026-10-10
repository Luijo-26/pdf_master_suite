@echo off
chcp 65001 > nul
echo ========================================================
echo   Compilando PDF Master Suite v2.2 a ejecutable (.exe)
echo ========================================================
echo.
echo 1. Verificando dependencias...
python -m pip install -r requirements.txt
echo.
echo 2. Compilando con PyInstaller...
if exist build rd /s /q build > nul 2>&1
python -m PyInstaller --onefile --noconsole --clean --hidden-import PySide6.QtPdf --hidden-import PySide6.QtSvg --hidden-import reportlab --hidden-import docx --hidden-import openpyxl --hidden-import win32com.client --name PDFMasterSuite_v2.2 main.py
echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo   [EXITO] Ejecutable generado en dist\PDFMasterSuite_v2.2.exe
    copy /Y dist\PDFMasterSuite_v2.2.exe dist\PDFMasterSuite.exe > nul
    echo.
    echo   Lanzando aplicacion...
    start "" "dist\PDFMasterSuite_v2.2.exe"
) else (
    echo   [ERROR] Fallo la compilacion.
)
echo ========================================================
pause
