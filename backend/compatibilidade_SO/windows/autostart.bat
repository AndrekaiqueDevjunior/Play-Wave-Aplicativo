@echo off
REM Registra o PlayWave Player para iniciar com o Windows
REM Execute como Administrador

set "EXE_PATH=C:\Program Files\PlayWave Player\PlayWave Player.exe"

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" ^
    /v "PlayWavePlayer" ^
    /t REG_SZ ^
    /d "\"%EXE_PATH%\"" ^
    /f

echo PlayWave Player registrado para iniciar com o Windows.
echo Caminho: %EXE_PATH%
pause
