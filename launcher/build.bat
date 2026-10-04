@echo off
REM Compila "RF Translator.exe" (lancador com pedido de administrador).
REM So precisa do compilador C# que vem com o Windows (.NET 4) - nao
REM precisa de Python instalado.
REM pushd/popd: quem chama (install.bat) fica na pasta onde estava.
pushd "%~dp0"
REM Textos na lingua da app (o install.bat ja os carregou).
if not defined M_BOK (
  chcp 65001 >nul
  call "%~dp0lang.bat"
)
if not exist ..\app.ico (
  if exist ..\python\python.exe ( ..\python\python.exe make_icon.py ) else ( py -3.13 make_icon.py )
)
"%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /codepage:65001 /target:winexe /optimize+ ^
  /win32manifest:app.manifest /win32icon:..\app.ico ^
  /reference:System.Windows.Forms.dll /reference:System.Drawing.dll ^
  /reference:System.IO.Compression.dll ^
  /reference:System.IO.Compression.FileSystem.dll ^
  /out:"..\RF Translator.exe" launcher.cs
if errorlevel 1 (echo %M_BERR% & popd & exit /b 1)
echo %M_BOK%
popd
