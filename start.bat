@echo off
REM ============================================================
REM  GoldenHour — One-Click Startup Script
REM  Starts both Backend (FastAPI) and Frontend (Vite/React)
REM  and connects them together automatically.
REM ============================================================
title GoldenHour Startup

echo.
echo  ========================================
echo   GoldenHour - Full Stack Startup
echo  ========================================
echo.

REM --- Step 1: Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Install Python 3.12+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found.

REM --- Step 2: Check Node.js ---
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo         Install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found.

REM --- Step 3: Setup Python virtual environment ---
echo.
echo [1/6] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo       Created .venv
) else (
    echo       .venv already exists, skipping creation.
)

REM --- Step 4: Install backend dependencies ---
echo [2/6] Installing backend dependencies...
call .venv\Scripts\activate.bat
pip install -e ".[dev]" --quiet 2>nul
echo       Backend dependencies installed.

REM --- Step 5: Create backend .env if missing ---
if not exist ".env" (
    echo [3/6] Creating backend .env from template...
    copy .env.example .env >nul
    echo       Created .env — edit secrets for production.
) else (
    echo [3/6] Backend .env already exists.
)

REM --- Step 6: Install frontend dependencies ---
echo [4/6] Installing frontend dependencies...
pushd goldenhour-app
call npm install --silent 2>nul
echo       Frontend dependencies installed.

REM --- Step 7: Configure frontend to connect to real backend ---
echo [5/6] Configuring frontend to connect to backend...
(
echo # ============================================================
echo # GoldenHour Environment Configuration
echo # ============================================================
echo.
echo # Toggle Mock Data Layer ^(false = connect to real backend^)
echo VITE_USE_MOCKS=false
echo.
echo # Backend API endpoint
echo VITE_API_URL=http://localhost:8000/api/v1
echo VITE_WS_URL=ws://localhost:8000/ws
echo.
echo # MapLibre Tile Server
echo VITE_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
) > .env
echo       Frontend configured to use real backend API.
popd

REM --- Step 8: Start both servers ---
echo [6/6] Starting servers...
echo.
echo  ========================================
echo   Starting Backend  : http://localhost:8000
echo   Starting Frontend : http://localhost:5173
echo   API Docs (Swagger): http://localhost:8000/docs
echo  ========================================
echo.
echo  Press Ctrl+C in each window to stop.
echo.

REM Start backend in a new terminal window
start "GoldenHour Backend (port 8000)" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait 3 seconds for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new terminal window
start "GoldenHour Frontend (port 5173)" cmd /k "cd /d %~dp0\goldenhour-app && npm run dev"

REM Wait 2 seconds then open browser
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo  [SUCCESS] Both servers are running!
echo.
echo  Frontend : http://localhost:5173
echo  Backend  : http://localhost:8000
echo  API Docs : http://localhost:8000/docs
echo.
echo  Close this window or press any key to exit.
echo  (The servers will keep running in their own windows)
echo.
pause
