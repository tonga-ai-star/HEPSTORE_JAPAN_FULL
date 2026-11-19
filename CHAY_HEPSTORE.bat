@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 start.py
if errorlevel 1 (
  echo Khong tim thay py? Thu cai Python 3.12 tu python.org, chon Add Python to PATH.
  pause
)
