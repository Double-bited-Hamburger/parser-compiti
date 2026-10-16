@echo off
rem Avvia Parser Compiti su Windows.
rem La prima volta prepara in .venv un ambiente Python tutto suo, con le librerie giuste: niente da installare a mano.
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto librerie

rem Il lanciatore "py" arriva con Python da python.org; altrimenti si prova "python".
set "BASE=py -3"
where py >nul 2>nul || set "BASE=python"
%BASE% -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>nul
if errorlevel 1 (
  echo Serve Python 3.12 o successivo: scaricalo da https://www.python.org/downloads/
  pause
  exit /b 1
)
echo Prima installazione: preparo l'ambiente Python, ci vuole qualche minuto...
%BASE% -m venv .venv
if errorlevel 1 goto errore

:librerie
rem Le librerie si (re)installano la prima volta e quando cambia requirements.txt (dopo un aggiornamento).
fc /b requirements.txt .venv\requisiti.txt >nul 2>nul
if not errorlevel 1 goto avvia
"%PY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto errore
copy /y requirements.txt .venv\requisiti.txt >nul

:avvia
"%PY%" main.py %*
if errorlevel 1 (
  pause
  exit /b 1
)
exit /b 0

:errore
echo.
echo Installazione non riuscita: controlla la connessione e i messaggi qui sopra.
pause
exit /b 1
