@echo off
title GoldenHour — All Services
color 0A

echo.
echo  ============================================
echo   GoldenHour Food Rescue Platform
echo   Starting all services...
echo  ============================================
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+
    pause
    exit /b 1
)

:: Check Node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node 18+
    pause
    exit /b 1
)

:: ──────────────────────────────────────────────
:: 1. Backend — FastAPI (port 8000)
:: ──────────────────────────────────────────────
echo [1/2] Starting Backend API (port 8000)...
cd /d "X:\Golden Hour\Ami-Hack"
start "GH-Backend" cmd /k "title GH-Backend (port 8000) && color 0B && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to be ready
timeout /t 3 /nobreak >nul

:: ──────────────────────────────────────────────
:: 2. Frontend — Vite (port 5173)
:: ──────────────────────────────────────────────
echo [2/2] Starting Frontend Dev Server (port 5173)...
cd /d "X:\Golden Hour\Ami-Hack\goldenhour-app"
start "GH-Frontend" cmd /k "title GH-Frontend (port 5173) && color 0E && npm run dev"

:: Wait for frontend to be ready
timeout /t 4 /nobreak >nul

:: ──────────────────────────────────────────────
:: Done
:: ──────────────────────────────────────────────
echo.
echo  ============================================
echo   All services started!
echo  ============================================
echo.
echo   Backend API:    http://localhost:8000
echo   Frontend App:   http://localhost:5173
echo   Health Check:   http://localhost:8000/healthz
echo   API Docs:       http://localhost:8000/docs
echo.
echo   Press any key to open the app in browser...
pause >nul

start http://localhost:5173
