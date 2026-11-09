@echo off
cd /d "%~dp0"
if "%~1"=="test" (
    python -m unittest discover -s tests -t . -v
) else (
    python -m src.main %*
)
