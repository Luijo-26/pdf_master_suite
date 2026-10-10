@echo off
setlocal

echo ========================================================
echo   [INSTALADOR] Compilando PDF Master Suite (Inno Setup)
echo ========================================================
echo.

:: 1. Detectar compilador de Inno Setup
set ISCC_PATH=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if not defined ISCC_PATH (
    where iscc >nul 2>&1
    if not errorlevel 1 for /f "delims=" %%i in ('where iscc') do set "ISCC_PATH=%%i"
)

if not defined ISCC_PATH (
    echo [ERROR] No se encontro Inno Setup.
    echo Puedes instalarlo ejecutando: winget install JRSoftware.InnoSetup
    pause
    exit /b 1
)

echo [INFO] Inno Setup detectado en:
echo        %ISCC_PATH%
echo.

if not exist assets\icon.ico (
    echo [INFO] Generando assets\icon.ico...
    python -c "import os; from PySide6.QtWidgets import QApplication; from ui.icons import logo_pixmap; from PIL import Image; app = QApplication([]); pm = logo_pixmap(256); os.makedirs('assets', exist_ok=True); pm.save('assets/icon_256.png'); img = Image.open('assets/icon_256.png'); img.save('assets/icon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])"
)

if exist build rd /s /q build > nul 2>&1
if exist dist\app_package rd /s /q dist\app_package > nul 2>&1
if not exist dist\installer mkdir dist\installer > nul 2>&1

echo [1/2] Compilando aplicacion en carpeta (--onedir)...
python -m PyInstaller --noconsole --clean ^
    --icon assets\icon.ico ^
    --distpath dist\app_package ^
    --hidden-import PySide6.QtPdf ^
    --hidden-import PySide6.QtPdfWidgets ^
    --hidden-import PySide6.QtSvg ^
    --hidden-import reportlab ^
    --hidden-import docx ^
    --hidden-import openpyxl ^
    --hidden-import win32com.client ^
    --name PDFMasterSuite main.py

if errorlevel 1 (
    echo.
    echo   [ERROR] Fallo la compilacion con PyInstaller.
    pause
    exit /b 1
)

echo installed > "dist\app_package\PDFMasterSuite\.installed"

echo.
echo [2/2] Generando el instalador con Inno Setup...
"%ISCC_PATH%" installer.iss

if errorlevel 1 (
    echo.
    echo   [ERROR] Fallo la generacion del instalador con Inno Setup.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   [EXITO] Instalador oficial generado en:
echo   Ubicacion: dist\installer\PDFMasterSuite_Setup.exe
echo ========================================================
echo.
if not "%1"=="--nopause" pause
