@echo off
chcp 65001 >nul 2>&1

:: Xianyu Monitor - Windows Startup Script

cd /d "%~dp0"

echo ========================================
echo   Xianyu Monitor - Windows Startup
echo ========================================
echo.
echo   [1] Quick Start  - start backend only
echo   [2] Full Build   - build frontend + start
echo   [3] Exit
echo.
echo ========================================

set /p "CHOICE=Select [1/2/3]: "

if "%CHOICE%" == "1" goto :quick
if "%CHOICE%" == "2" goto :full
if "%CHOICE%" == "3" exit /b 0
echo Invalid choice.
pause
exit /b 1

:quick
set "QUICK_MODE=1"
echo.
echo   Mode: QUICK - skip build, start backend only
goto :check_env

:full
set "QUICK_MODE=0"
echo.
echo   Mode: FULL - build frontend + start backend
goto :check_env

:: [1/6] Check environment
:check_env
echo.
echo [1/6] Checking environment...

set "PYTHON_CMD="
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3"
    goto :py_ok
)
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto :py_ok
)
echo   [MISSING] Python 3.10+
goto :show_help

:py_ok
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [MISSING] Python version must be 3.10+
    goto :show_help
)

%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [MISSING] pip
    goto :show_help
)

if "%QUICK_MODE%" == "1" goto :env_ok

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [MISSING] Node.js
    goto :show_help
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo   [MISSING] npm
    goto :show_help
)

:env_ok
echo [OK] Environment check passed
goto :step2

:show_help
echo.
echo Fix:
echo   1. Install Python:  winget install Python.Python.3.11
echo   2. Install Node.js: winget install OpenJS.NodeJS.LTS
echo   3. Install Playwright:
echo      python -m pip install playwright
echo      python -m playwright install chromium
echo   4. Install browser:  winget install Google.Chrome
echo   5. Config (optional): copy .env.example .env
echo.
pause
exit /b 1

:step2
if "%QUICK_MODE%" == "1" goto :step_pip

:: [2/6] Clean old build
echo.
echo [2/6] Cleaning old build...
if exist "dist" (
    rmdir /s /q "dist"
    echo [OK] Removed old dist directory
) else (
    echo [OK] No dist directory, skipped
)

:step_pip
:: [3/6] Install Python dependencies
echo.
echo [3/6] Installing Python dependencies...
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

%PYTHON_CMD% -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Python dependency installation failed
    pause
    exit /b 1
)
echo [OK] Python dependencies installed

if "%QUICK_MODE%" == "1" goto :start_server

:: [4/6] Build frontend
echo.
echo [4/6] Building frontend...
if not exist "web-ui" (
    echo [ERROR] web-ui directory not found
    pause
    exit /b 1
)

pushd web-ui

if not exist "node_modules" (
    echo First run, installing frontend dependencies...
    call npm install
    if %errorlevel% neq 0 (
        popd
        echo [ERROR] Frontend dependency installation failed
        pause
        exit /b 1
    )
)

echo Building frontend...
call npm run build
if %errorlevel% neq 0 (
    popd
    echo [ERROR] Frontend build failed
    pause
    exit /b 1
)

popd

if not exist "dist" (
    echo [ERROR] Build failed, dist directory not created
    pause
    exit /b 1
)

echo [OK] Frontend build complete

:: [5/6] Verify build
echo.
echo [5/6] Verifying build output...
echo [OK] Build output at dist/

:start_server
:: [6/6] Start backend
echo.
echo [6/6] Starting backend service...
echo ========================================
echo   URL:  http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo ========================================
echo.

%PYTHON_CMD% -m src.app

echo.
echo Service stopped.
pause
