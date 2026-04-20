@echo off
cd /d %~dp0
call .\.venv\Scripts\activate
python .\groupalarm_cli.py
pause