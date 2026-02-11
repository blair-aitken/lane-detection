@echo off
setlocal EnableExtensions

cd /d "%~dp0\.."

echo ------------------------------------------------------------
echo [0/6] Pre-flight Checks
echo ------------------------------------------------------------

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    goto python_ok
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto python_ok
)

echo ERROR: Python 3.9+ not found.
pause
exit /b 1

:python_ok
for /f "tokens=2" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set PYVER=%%v
echo Using Python %PYVER% (%PYTHON_CMD%)

echo.
echo Running vehicle configuration...
%PYTHON_CMD% -c "from src import config; config.ensure_vehicle_config()"
if errorlevel 1 (
    echo Vehicle configuration failed.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------
echo [1/6] Environment Setup
echo ------------------------------------------------------------

if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo ------------------------------------------------------------
echo [2/6] Verify Tkinter Support
echo ------------------------------------------------------------

venv\Scripts\python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Tkinter not available in virtual environment.
    pause
    exit /b 1
) else (
    echo Tkinter available in virtual environment.
)

echo.
echo ------------------------------------------------------------
echo [3/6] Install Dependencies
echo ------------------------------------------------------------

venv\Scripts\python -m pip install --upgrade pip
venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------
echo [4/6] Calibrate Camera Intrinsics
echo ------------------------------------------------------------

if not exist data\calib\camera_intrinsics.npz (
    venv\Scripts\python scripts\run_calibration.py
    if errorlevel 1 (
        echo Calibration failed.
        pause
        exit /b 1
    )
) else (
    echo Using existing camera_intrinsics.npz
)

echo.
echo ------------------------------------------------------------
echo [5/6] Compute Homography Matrix
echo ------------------------------------------------------------

if not exist data\calib\camera_intrinsics.npz (
    echo ERROR: Camera intrinsics not found.
    echo Homography generation requires camera calibration first.
    pause
    exit /b 1
)

set /p yn="Generate a new homography matrix? (y/n): "
echo.

if /I "%yn%"=="Y" (
    venv\Scripts\python scripts\run_homography.py
    if errorlevel 1 (
        echo Homography failed.
        pause
        exit /b 1
    )
) else (
    echo Skipping homography generation.
)

echo.
echo ------------------------------------------------------------
echo [6/6] Calculate Lateral Position
echo ------------------------------------------------------------

venv\Scripts\python scripts\run_measurement.py
if errorlevel 1 (
    echo Measurement failed.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------------------
echo Pipeline complete.
echo Outputs:
echo   - CSV results:  output\csv
echo   - Debug videos: output\videos
echo ------------------------------------------------------------
pause
exit /b 0