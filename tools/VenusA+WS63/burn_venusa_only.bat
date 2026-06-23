@echo off
setlocal
cd /d "%~dp0"
call "%~dp0run.bat" %* --skip-ws63
exit /b %ERRORLEVEL%
