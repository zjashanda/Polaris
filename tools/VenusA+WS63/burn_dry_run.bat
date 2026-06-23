@echo off
setlocal
cd /d "%~dp0"
call "%~dp0run.bat" %* --dry-run
exit /b %ERRORLEVEL%
