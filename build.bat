@echo off
chcp 65001 > nul
echo ========================================================
echo   Compilando PDF Master Suite v2.1 a ejecutable (.exe)
echo ========================================================
echo.
echo 1. Verificando dependencias...
python -m pip install -r requirements.txt
echo.
echo 2. Compilando con PyInstaller...
python -m PyInstaller --onefile --noconsole --clean --hidden-import PySide6.QtPdf --hidden-import PySide6.QtSvg --name PDFMasterSuite_v2.1 main.py
echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo   [EXITO] Ejecutable generado en dist\PDFMasterSuite_v2.1.exe
    copy /Y dist\PDFMasterSuite_v2.1.exe dist\PDFMasterSuite.exe > nul
) else (
    echo   [ERROR] Fallo la compilacion.
)
echo ========================================================
pause
