@echo off
echo ===================================================
echo Page Change Monitor - Test Runner
echo ===================================================

:: Try to find python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not found in your PATH.
    echo Please install Python 3 and ensure "Add Python to PATH" is checked.
    echo.
    pause
    exit /b 1
)

echo Installing test dependencies...
:: Use 'python -m pip' instead of just 'pip' to avoid PATH issues
python -m pip install pytest pytest-mock
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies. 
    echo Try running: python -m pip install pytest pytest-mock
    pause
    exit /b 1
)

echo.
echo Running tests...
python -m pytest tests
echo.

if %errorlevel% equ 0 (
    echo SUCCESS: All tests passed!
) else (
    echo FAILURE: Some tests failed. See output above.
)

pause