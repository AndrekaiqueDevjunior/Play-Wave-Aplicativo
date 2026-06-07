@echo off
REM PlayWave Electron Development Launcher — Windows
REM Script que abre 4 terminais para rodar dev, preview, electron

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  PlayWave Electron Development Setup                        ║
echo ║                                                              ║
echo ║  Este script vai abrir 4 terminais:                         ║
echo ║  1. Terminal 1: Backend (Docker) - já deve estar rodando    ║
echo ║  2. Terminal 2: Frontend Dev Server (localhost:5173)        ║
echo ║  3. Terminal 3: Frontend Preview Server (localhost:3000)    ║
echo ║  4. Terminal 4: Electron App                                ║
echo ║                                                              ║
echo ║  Pré-requisito:                                             ║
echo ║  - Docker rodando (docker-compose up -d)                   ║
echo ║  - Node.js 18+                                              ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Verificar se está na pasta correta
if not exist "frontend\package.json" (
    echo ❌ Erro: Não encontrei frontend\package.json
    echo Executar este script da raiz do projeto
    exit /b 1
)

echo ✅ Estrutura do projeto validada
echo.
echo [1/4] Abrindo Terminal 1: Backend Status
start "Backend Check" cmd /k "docker ps && echo. && echo ✓ Docker containers rodando && pause"

echo [2/4] Abrindo Terminal 2: Frontend Dev (port 5173)
echo Aguardando 3 segundos...
timeout /t 3 /nobreak
start "Frontend Dev" cmd /k "cd /d "%CD%\frontend" && npm run dev"

echo [3/4] Abrindo Terminal 3: Preview Server (port 3000)
echo Aguardando 3 segundos...
timeout /t 3 /nobreak
start "Preview Server" cmd /k "cd /d "%CD%\frontend" && npm run preview -- --port 3000"

echo [4/4] Abrindo Terminal 4: Electron App
echo Aguardando 3 segundos...
timeout /t 3 /nobreak
start "Electron App" cmd /k "cd /d "%CD%\frontend\electron" && npm run dev"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║  Todos os terminais abertos!                                ║
echo ║                                                              ║
echo ║  URLs:                                                       ║
echo ║  - Frontend Dev: http://localhost:5173                      ║
echo ║  - Preview:      http://localhost:3000                      ║
echo ║  - Backend API:  http://localhost:8000                      ║
echo ║  - Health Check: http://localhost:8000/health               ║
echo ║                                                              ║
echo ║  Login:                                                      ║
echo ║  Email: admin@playwave.com                                  ║
echo ║  Senha: &2p0Kw45A&lLNX4bM%gpH*cy                              ║
echo ║                                                              ║
echo ║  Debug Electron:                                            ║
echo ║  Ctrl+Shift+I = DevTools                                    ║
echo ║  Ctrl+Shift+R = Reload                                      ║
echo ║  Ctrl+Q       = Quit                                        ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Script finalizado. Os terminais continuarão abertos.
timeout /t 5 /nobreak
