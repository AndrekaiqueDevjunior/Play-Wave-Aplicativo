@echo off
REM =============================================================================
REM PlayWave Player — Build Windows (.exe)
REM =============================================================================

setlocal
set "ROOT_DIR=%~dp0..\..\..\"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "ELECTRON_DIR=%FRONTEND_DIR%\electron"

echo [1/4] Build do frontend React
cd /d "%FRONTEND_DIR%"
call npm install --legacy-peer-deps
set VITE_PLAYER_MODE=electron
call npm run build
if errorlevel 1 goto :error

echo [2/4] Instalar dependencias do Electron
cd /d "%ELECTRON_DIR%"
call npm install
if errorlevel 1 goto :error

echo [3/4] Build Windows
call npm run build:win
if errorlevel 1 goto :error

echo [4/4] Pronto!
echo Arquivos gerados em: %ELECTRON_DIR%\dist-electron\
dir "%ELECTRON_DIR%\dist-electron\"
goto :end

:error
echo ERRO no build!
exit /b 1

:end
endlocal
