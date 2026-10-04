@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
REM Textos na lingua da app (ui_prefs.json).
call "%~dp0launcher\lang.bat"

echo ================================================
echo   RF Online Translator
echo ================================================
echo.
echo %M_RUN%
echo.

REM O Python da app (pasta python\); senao um Python 3.13 instalado.
if exist python\python.exe (
  python\python.exe main.py %*
) else (
  py -3.13 main.py %*
)

echo.
echo ================================================
echo   %M_END%
echo ================================================
pause
endlocal
