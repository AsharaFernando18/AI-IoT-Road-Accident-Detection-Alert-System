@echo off
REM RoadSafeNet Setup Script for Windows

echo =========================================
echo RoadSafeNet Setup Script
echo =========================================
echo.

REM Check Python
echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo Python found

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
echo Virtual environment created

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo Dependencies installed

REM Install Prisma
echo.
echo Installing Prisma...
pip install prisma
echo Prisma installed

REM Generate Prisma client
echo.
echo Generating Prisma client...
prisma generate --schema=database/schema.prisma
echo Prisma client generated

REM Create .env file
if not exist .env (
    echo.
    echo Creating .env file...
    copy .env.example .env
    echo .env file created - Please edit with your configuration!
) else (
    echo.
    echo .env file already exists
)

REM Create directories
echo.
echo Creating directories...
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist ai_model\models mkdir ai_model\models
if not exist cache\huggingface mkdir cache\huggingface
echo Directories created

REM Initialize database
echo.
echo Initializing database...
python database/init_db.py
echo Database initialized

echo.
echo =========================================
echo Installation Complete!
echo =========================================
echo.
echo Next steps:
echo 1. Configure your .env file with Telegram bot token
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the application:
echo    - Detection: python main.py
echo    - Dashboard: python frontend/app.py
echo    - API: python backend/api.py
echo.
echo Documentation: README.md
echo =========================================
pause
