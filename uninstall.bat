@echo off
setlocal enabledelayedexpansion

title Uninstall RoadBookMaker

echo.
echo ============================================================
echo           Uninstalling RoadBookMaker
echo ============================================================
echo.

REM 1. Confirmation prompt
set /p "CONFIRM=Do you really want to remove RoadBookMaker and its dependencies? (Y/N): "
if /i "%CONFIRM%" neq "Y" (
    echo [INFO] Uninstallation cancelled.
    pause
    exit /b
)

REM 2. Get current directory (installation folder)
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo.
echo [INFO] Folder to clean: %INSTALL_DIR%

REM 3. Close running python processes if any
echo [INFO] Closing associated Python processes...
taskkill /FI "WINDOWTITLE eq RoadBookMaker*" /F >nul 2>&1

REM 4. Remove virtual environment
if exist "%INSTALL_DIR%\.venv" (
    echo [INFO] Removing virtual environment (.venv)...
    rmdir /s /q "%INSTALL_DIR%\.venv"
    if %errorlevel% eq 0 (
        echo [OK] Virtual environment removed.
    ) else (
        echo [WARNING] Could not completely remove .venv (files locked?).
    )
)

REM 5. Remove core application files and Desktop shortcut
echo [INFO] Removing application files...
if exist "%INSTALL_DIR%\router_app.py" del /q "%INSTALL_DIR%\router_app.py"
if exist "%INSTALL_DIR%\requirements.txt" del /q "%INSTALL_DIR%\requirements.txt"
if exist "%INSTALL_DIR%\imoca_polar.csv" del /q "%INSTALL_DIR%\imoca_polar.csv"
if exist "%INSTALL_DIR%\run.bat" del /q "%INSTALL_DIR%\run.bat"
if exist "%INSTALL_DIR%\Lancer_Application.bat" del /q "%INSTALL_DIR%\Lancer_Application.bat"

REM Remove Desktop shortcut if it exists
if exist "%USERPROFILE%\Desktop\RoadBookMaker.lnk" (
    echo [INFO] Removing Desktop shortcut...
    del /q "%USERPROFILE%\Desktop\RoadBookMaker.lnk"
    if %errorlevel% eq 0 (
        echo [OK] Desktop shortcut removed.
    )
)

if exist "%INSTALL_DIR%\uninstall.bat" del /q "%INSTALL_DIR%\uninstall.bat"

REM 6. Propose full folder purge
echo.
set /p "PURGE=Do you also want to completely delete the installation folder %INSTALL_DIR%? (Y/N): "
if /i "%PURGE%"=="Y" (
    cd ..
    rmdir /s /q "%INSTALL_DIR%"
    echo [OK] RoadBookMaker directory successfully deleted.
)

echo.
echo Uninstallation complete.
pause
