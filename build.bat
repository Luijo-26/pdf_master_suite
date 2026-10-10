@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ========================================================
echo             PDF MASTER SUITE - CENTRO DE BUILD
echo ========================================================
echo.
echo   Selecciona el tipo de version que deseas compilar:
echo.
echo     [1] Version PORTABLE (.exe unico independiente)
echo     [2] Version INSTALADOR (Setup para Windows con Inno Setup)
echo     [3] AMBAS versiones (Preparar para GitHub Releases)
echo     [4] Salir
echo.
echo ========================================================
set /p OPCION="Elige una opcion (1-4): "

if "%OPCION%"=="1" goto build_port
if "%OPCION%"=="2" goto build_inst
if "%OPCION%"=="3" goto build_both
if "%OPCION%"=="4" goto fin

echo.
echo Opcion invalida. Intenta nuevamente.
timeout /t 2 > nul
goto menu

:build_port
call build_portable.bat
goto fin

:build_inst
call build_installer.bat
goto fin

:build_both
echo.
echo ========================================================
echo   Compilando AMBAS versiones para lanzamiento
echo ========================================================
echo.
call build_portable.bat --nopause
call build_installer.bat --nopause
echo.
echo ========================================================
echo   [COMPLETO] Ambas versiones compiladas exitosamente:
echo   - Portable:   dist\portable\PDFMasterSuite_Portable.exe
echo   - Instalador: dist\installer\PDFMasterSuite_Setup.exe
echo ========================================================
pause
goto fin

:fin
