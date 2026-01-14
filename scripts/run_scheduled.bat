@echo off
REM Price Discrepancy Email Processor - Scheduled Run (last 24 hours)
REM To be used with Windows Task Scheduler

cd /d "%~dp0\.."
python -m src.main --auto >> logs\scheduled_run.log 2>&1
