@echo off
setlocal enabledelayedexpansion

title Install and Run - RoadBookMaker

REM 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to Windows PATH.
    echo Please install Python from https://www.python.org/ and check "Add Python to PATH".
    pause
    exit /b
)

REM 2. Choose installation directory
set "DEFAULT_INSTALL_DIR=%LOCALAPPDATA%\RoadBookMaker"
echo.
echo ============================================================
echo          RoadBookMaker Installation Directory
echo ============================================================
echo Default directory : %DEFAULT_INSTALL_DIR%
echo.
set /p "TARGET_DIR=Press ENTER to accept or type another path: "

if "%TARGET_DIR%"=="" set "TARGET_DIR=%DEFAULT_INSTALL_DIR%"

echo.
echo [INFO] Selected directory : %TARGET_DIR%

REM 3. Create target directory if it doesn't exist
if not exist "%TARGET_DIR%" (
    echo [INFO] Creating installation directory...
    mkdir "%TARGET_DIR%" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create folder %TARGET_DIR%. Check permissions.
        pause
        exit /b
    )
)

REM 4. Copy source files to installation directory
echo [INFO] Copying application files...
copy /Y "router_app.py" "%TARGET_DIR%\" >nul
copy /Y "imoca_polar.csv" "%TARGET_DIR%\" >nul 2>&1
if exist "requirements.txt" copy /Y "requirements.txt" "%TARGET_DIR%\" >nul
if exist "uninstall.bat" copy /Y "uninstall.bat" "%TARGET_DIR%\" >nul
if exist "%~nx0" copy /Y "%~nx0" "%TARGET_DIR%\" >nul

cd /d "%TARGET_DIR%"

REM 5. Create Desktop Shortcut using PowerShell
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\RoadBookMaker.lnk"
if not exist "%SHORTCUT_PATH%" (
    echo [INFO] Creating Desktop shortcut...
    powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath='%TARGET_DIR%\run.bat'; $s.WorkingDirectory='%TARGET_DIR%'; $s.Save()" >nul 2>&1
    if %errorlevel% eq 0 (
        echo [OK] Desktop shortcut successfully created!
    ) else (
        echo [WARNING] Could not create Desktop shortcut.
    )
)

REM 6. Create and activate virtual environment (.venv)
if not exist ".venv" (
    echo [INFO] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create .venv.
        pause
        exit /b
    )
    echo [OK] Virtual environment created.
)

call .venv\Scripts\activate.bat

REM 7. Install dependencies
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install packages.
        pause
        exit /b
    )
    echo [OK] Dependencies up to date.
)

REM 8. Launch application
echo [INFO] Launching RoadBookMaker...
python router_app.py

pause
