@echo off
setlocal
cd /d "%~dp0"
call "%~dp0run.bat" %* --skip-venusa
exit /b %ERRORLEVEL%
