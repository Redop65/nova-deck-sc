@echo off
call "%~dp0start.bat" --test-mode
exit /b %errorlevel%
