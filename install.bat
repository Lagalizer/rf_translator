@echo off
REM ===== RF Translator - Instalador Windows =====
REM Nao precisa de Python instalado: cria o "RF Translator.exe" e este
REM descarrega o Python proprio da app para a pasta "python\" (tudo fica
REM dentro da pasta da app). Primeiro pergunta a lingua: a app, a janela
REM de instalacao e os terminais ficam nessa lingua (ui_prefs.json).
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================================
echo   RF Online Translator
echo ================================================
echo.
echo   1  English
echo   2  Português
echo   3  Español
echo   4  Français
echo   5  Deutsch
echo   6  Русский
echo   7  Italiano
echo.
REM RF_LANG=pt (por exemplo) salta a pergunta (testes, instalacao sem
REM ninguem ao teclado).
if defined RF_LANG (
  set "L=%RF_LANG%"
) else (
  choice /c 1234567 /n /m "Language / Língua / Язык [1-7]: "
  call :pick
)

REM Guarda a lingua (mantem o tema, se ja havia ui_prefs.json). Uma
REM chave por linha, como a app grava: assim o findstr le cada uma.
set "TH=dark"
if exist ui_prefs.json (
  for /f "tokens=2 delims=:," %%a in ('findstr /c:"\"theme\"" ui_prefs.json') do set "TH=%%~a"
)
set "TH=%TH: =%"
set "TH=%TH:"=%"
if not "%TH%"=="light" if not "%TH%"=="system" set "TH=dark"
(
  echo {
  echo   "lang": "%L%",
  echo   "theme": "%TH%"
  echo }
) > ui_prefs.json

call "%~dp0launcher\lang.bat"
echo.

echo %M_S1%
call "%~dp0launcher\build.bat"
if errorlevel 1 (echo %M_E1% & pause & exit /b 1)
REM O build.bat muda de pasta: volta a pasta da app.
cd /d "%~dp0"

echo %M_S2%
"%~dp0RF Translator.exe" --setup-only
if errorlevel 1 (echo %M_E2% & pause & exit /b 1)

echo.
echo ================================================
echo  %M_DONE%
echo  %M_OPEN%
echo ================================================
pause
exit /b 0

:pick
set "L=en"
if errorlevel 7 (set "L=it" & goto :eof)
if errorlevel 6 (set "L=ru" & goto :eof)
if errorlevel 5 (set "L=de" & goto :eof)
if errorlevel 4 (set "L=fr" & goto :eof)
if errorlevel 3 (set "L=es" & goto :eof)
if errorlevel 2 (set "L=pt" & goto :eof)
goto :eof
