@echo off
setlocal

echo ========================================================
echo   [PORTABLE] Compilando PDF Master Suite (Ejecutable unico)
echo ========================================================
echo.

if not exist assets\icon.ico (
    echo [INFO] Generando assets\icon.ico...
    python -c "import os; from PySide6.QtWidgets import QApplication; from ui.icons import logo_pixmap; from PIL import Image; app = QApplication([]); pm = logo_pixmap(256); os.makedirs('assets', exist_ok=True); pm.save('assets/icon_256.png'); img = Image.open('assets/icon_256.png'); img.save('assets/icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])"
)

if exist build rd /s /q build > nul 2>&1
if not exist dist\portable mkdir dist\portable > nul 2>&1

echo [1/1] Compilando ejecutable portable en dist\portable...
python -m PyInstaller --onefile --noconsole --clean ^
    --icon assets\icon.ico ^
    --distpath dist\portable ^
    --hidden-import PySide6.QtPdf ^
    --hidden-import PySide6.QtPdfWidgets ^
    --hidden-import PySide6.QtSvg ^
    --hidden-import reportlab ^
    --hidden-import docx ^
    --hidden-import openpyxl ^
    --hidden-import win32com.client ^
    --name PDFMasterSuite_Portable main.py

if errorlevel 1 (
    echo.
    echo   [ERROR] Fallo la compilacion portable.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   [EXITO] Version Portable lista en:
echo   Ubicacion: dist\portable\PDFMasterSuite_Portable.exe
echo ========================================================
echo.
if not "%1"=="--nopause" pause
