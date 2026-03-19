@echo off
echo AI Workforce Automation Platform - Setup
echo.

where python >nul 2>&1 || (echo Python not found & exit /b 1)
where node >nul 2>&1 || (echo Node.js not found & exit /b 1)

echo Setting up backend...
cd backend
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt -q
echo Backend ready.

echo Seeding database...
cd ..\scripts
python seed_db.py

echo Setting up frontend...
cd ..\frontend
call npm install --silent
echo Frontend ready.

echo.
echo Setup complete!
echo Start with:
echo   1. ollama serve
echo   2. cd backend ^& .venv\Scripts\activate ^& uvicorn main:app --reload
echo   3. cd frontend ^& npm run dev
echo   4. Open http://localhost:5173
