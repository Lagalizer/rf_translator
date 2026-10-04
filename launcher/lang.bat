@echo off
REM Textos dos terminais (install.bat, run.bat, build.bat) na lingua da
REM app. Usa a variavel L (en/pt/es/fr/de/ru/it); sem ela, le o
REM "lang" do ui_prefs.json (o mesmo ficheiro que a app usa).
REM Este ficheiro esta em UTF-8: quem o chama faz antes "chcp 65001".
if not defined L (
  set "L=en"
  if exist "%~dp0..\ui_prefs.json" (
    for /f "tokens=2 delims=:," %%a in ('findstr /c:"\"lang\"" "%~dp0..\ui_prefs.json"') do set "L=%%~a"
  )
)
set "L=%L: =%"
set "L=%L:"=%"

REM Ingles (tambem o que fica se faltar alguma traducao)
set "M_S1=[1/2] Creating "RF Translator.exe"..."
set "M_E1=ERROR: could not create the .exe"
set "M_S2=[2/2] Preparing the app's own Python - first time only, a few minutes..."
set "M_E2=ERROR: see the message that appeared"
set "M_DONE=Installation finished!"
set "M_OPEN=Open the app with:  RF Translator.exe"
set "M_BOK=OK: "RF Translator.exe" created."
set "M_BERR=ERROR while compiling"
set "M_RUN=Checking dependencies - this can take a while the first time..."
set "M_END=App closed."

if "%L%"=="pt" (
  set "M_S1=[1/2] A criar o "RF Translator.exe"..."
  set "M_E1=ERRO: não foi possível criar o .exe"
  set "M_S2=[2/2] A preparar o Python da app - só da 1.ª vez, uns minutos..."
  set "M_E2=ERRO: vê a mensagem que apareceu"
  set "M_DONE=Instalação concluída!"
  set "M_OPEN=Abre a app com:  RF Translator.exe"
  set "M_BOK=OK: "RF Translator.exe" criado."
  set "M_BERR=ERRO a compilar"
  set "M_RUN=A verificar dependências - pode demorar na 1.ª vez..."
  set "M_END=App terminada."
)
if "%L%"=="es" (
  set "M_S1=[1/2] Creando "RF Translator.exe"..."
  set "M_E1=ERROR: no se pudo crear el .exe"
  set "M_S2=[2/2] Preparando el Python de la app - solo la 1.ª vez, unos minutos..."
  set "M_E2=ERROR: mira el mensaje que apareció"
  set "M_DONE=¡Instalación terminada!"
  set "M_OPEN=Abre la app con:  RF Translator.exe"
  set "M_BOK=OK: "RF Translator.exe" creado."
  set "M_BERR=ERROR al compilar"
  set "M_RUN=Comprobando dependencias - puede tardar la 1.ª vez..."
  set "M_END=App cerrada."
)
if "%L%"=="fr" (
  set "M_S1=[1/2] Création de "RF Translator.exe"..."
  set "M_E1=ERREUR : impossible de créer le .exe"
  set "M_S2=[2/2] Préparation du Python de l'app - seulement la 1re fois, quelques minutes..."
  set "M_E2=ERREUR : regarde le message qui est apparu"
  set "M_DONE=Installation terminée !"
  set "M_OPEN=Ouvre l'app avec :  RF Translator.exe"
  set "M_BOK=OK : "RF Translator.exe" créé."
  set "M_BERR=ERREUR de compilation"
  set "M_RUN=Vérification des dépendances - peut être long la 1re fois..."
  set "M_END=App fermée."
)
if "%L%"=="de" (
  set "M_S1=[1/2] "RF Translator.exe" wird erstellt..."
  set "M_E1=FEHLER: die .exe konnte nicht erstellt werden"
  set "M_S2=[2/2] Das Python der App wird vorbereitet - nur beim 1. Mal, ein paar Minuten..."
  set "M_E2=FEHLER: siehe die angezeigte Meldung"
  set "M_DONE=Installation abgeschlossen!"
  set "M_OPEN=Öffne die App mit:  RF Translator.exe"
  set "M_BOK=OK: "RF Translator.exe" erstellt."
  set "M_BERR=FEHLER beim Kompilieren"
  set "M_RUN=Abhängigkeiten werden geprüft - kann beim 1. Mal dauern..."
  set "M_END=App beendet."
)
if "%L%"=="ru" (
  set "M_S1=[1/2] Создание "RF Translator.exe"..."
  set "M_E1=ОШИБКА: не удалось создать .exe"
  set "M_S2=[2/2] Подготовка Python приложения - только в первый раз, несколько минут..."
  set "M_E2=ОШИБКА: смотрите появившееся сообщение"
  set "M_DONE=Установка завершена!"
  set "M_OPEN=Запускайте приложение через:  RF Translator.exe"
  set "M_BOK=OK: "RF Translator.exe" создан."
  set "M_BERR=ОШИБКА компиляции"
  set "M_RUN=Проверка зависимостей - в первый раз может занять время..."
  set "M_END=Приложение закрыто."
)
if "%L%"=="it" (
  set "M_S1=[1/2] Creazione di "RF Translator.exe"..."
  set "M_E1=ERRORE: impossibile creare il .exe"
  set "M_S2=[2/2] Preparazione del Python dell'app - solo la 1a volta, qualche minuto..."
  set "M_E2=ERRORE: guarda il messaggio apparso"
  set "M_DONE=Installazione completata!"
  set "M_OPEN=Apri l'app con:  RF Translator.exe"
  set "M_BOK=OK: "RF Translator.exe" creato."
  set "M_BERR=ERRORE di compilazione"
  set "M_RUN=Verifica delle dipendenze - può richiedere tempo la 1a volta..."
  set "M_END=App chiusa."
)
