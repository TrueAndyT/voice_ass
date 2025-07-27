@echo off
setlocal enabledelayedexpansion

echo 🛠️ Bootstrapping Voice Assistant Project for Windows...

:: Step 1: Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.10+ and try again.
    exit /b 1
)

:: Step 2: Create virtual environment
if not exist venv (
    echo 🐍 Creating virtual environment...
    python -m venv venv
) else (
    echo ✅ Virtual environment already exists.
)

:: Step 3: Activate virtual environment
echo ⚙️ Activating virtual environment...
call venv\Scripts\activate

:: Step 4: Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

:: Step 5: Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

echo ✅ Bootstrap complete.
echo To activate your environment in the future, run:
echo     venv\Scripts\activate
