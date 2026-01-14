@echo off
REM Price Discrepancy Email Processor - Manual Run
REM Usage: run_manual.bat [--date YYYY-MM-DD] [--date-from YYYY-MM-DD --date-to YYYY-MM-DD] [--dry-run]

cd /d "%~dp0\.."
python -m src.main %*
