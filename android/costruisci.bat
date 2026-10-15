@echo off
rem Costruisce l'APK dell'app Android e lo copia in output\registro.apk (vedi ANDROID.md).
cd /d "%~dp0"
rem Gradle vuole il Java di Android Studio: quello di sistema puo' essere troppo nuovo.
if exist "%ProgramFiles%\Android\Android Studio\jbr\bin\java.exe" set "JAVA_HOME=%ProgramFiles%\Android\Android Studio\jbr"
call "%~dp0gradlew.bat" assembleRelease
if errorlevel 1 (
  echo.
  echo Build non riuscita: controlla i messaggi qui sopra e ANDROID.md.
  pause
  exit /b 1
)
if not exist ..\output mkdir ..\output
copy /y app\build\outputs\apk\release\app-release.apk ..\output\registro.apk >nul
echo.
echo APK pronto: output\registro.apk
