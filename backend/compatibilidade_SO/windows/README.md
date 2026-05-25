# PlayWave Player — Windows (.exe)

## Stack
- **Electron 28+** empacotando o frontend React (`/player`)
- **electron-builder** gerando instalador NSIS (.exe) e versão portátil
- **Auto-start** via registro do Windows

## Pré-requisitos

```cmd
REM Node.js 18+
node --version

REM Instalar dependências
cd frontend\electron
npm install
```

## Build

```cmd
REM 1. Compilar frontend
cd frontend
npm run build

REM 2. Gerar .exe
cd electron
npm run build:win

REM Saída: electron\dist-electron\
REM   PlayWave Player Setup 3.1.0.exe    (instalador NSIS)
REM   PlayWave Player 3.1.0.exe          (portátil)
```

## Variáveis de ambiente

Crie um arquivo `.env` na pasta do executável:

```env
VITE_API_URL=http://SEU_SERVIDOR:8000
PLAYER_KIOSK=true
NODE_ENV=production
```

Ou passe via linha de comando:

```cmd
set VITE_API_URL=http://SEU_SERVIDOR:8000
set PLAYER_KIOSK=true
"PlayWave Player.exe"
```

## Auto-start no Windows

```cmd
REM Adicionar ao registro para iniciar com o sistema
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" ^
    /v "PlayWavePlayer" ^
    /t REG_SZ ^
    /d "\"C:\Program Files\PlayWave Player\PlayWave Player.exe\"" ^
    /f
```

## Modo Kiosk / Apresentação

O executável abre automaticamente em fullscreen/kiosk.
Para desativar kiosk (modo desenvolvedor):

```cmd
set PLAYER_KIOSK=false
"PlayWave Player.exe"
```

## Compatibilidade
- Windows 10 (x64)
- Windows 11 (x64)
- Processadores Intel / AMD / ARM64 (surface)
