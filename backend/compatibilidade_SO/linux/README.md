# PlayWave Player — Linux (AppImage / .deb / .rpm)

## Stack
- **Electron 28+** empacotando o frontend React (`/player`)
- **electron-builder** gerando AppImage, .deb e .rpm
- **Auto-start** via systemd service

## Pré-requisitos

```bash
# Node.js 18+
node --version

# Instalar dependências do Electron
cd frontend/electron
npm install
```

## Build

```bash
# Compilar frontend
cd frontend
npm run build         # gera frontend/dist/

# Gerar AppImage + deb
cd electron
npm run build:linux
# Saída: electron/dist-electron/
#   PlayWave Player-3.1.0.AppImage
#   playwave-player_3.1.0_amd64.deb
#   playwave-player-3.1.0.x86_64.rpm  (se rpmbuild disponível)
```

## Executar em modo kiosk

```bash
PLAYER_KIOSK=true VITE_PLAYER_URL=http://SEU_SERVIDOR/player ./PlayWave\ Player-3.1.0.AppImage
```

## Variáveis de ambiente

| Variável          | Padrão                           | Descrição                        |
|-------------------|----------------------------------|----------------------------------|
| VITE_API_URL      | http://localhost:8000            | URL da API backend               |
| VITE_PLAYER_URL   | http://localhost:3000/player     | URL do player (quando separado)  |
| PLAYER_KIOSK      | true                             | Ativa modo kiosk fullscreen      |
| NODE_ENV          | production                       | Ambiente                         |

## Auto-start no boot (systemd)

Salve em `/etc/systemd/system/playwave-player.service`:

```ini
[Unit]
Description=PlayWave Digital Signage Player
After=graphical-session.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=PLAYER_KIOSK=true
Environment=VITE_API_URL=http://SEU_SERVIDOR:8000
ExecStart=/opt/playwave/PlayWave Player-3.1.0.AppImage
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable playwave-player
sudo systemctl start playwave-player
```

## TV Box Linux (ARM)

```bash
# Build ARM64
cd frontend/electron
npm run build:linux -- --arm64
```

## Compatibilidade testada
- Ubuntu 20.04 / 22.04 / 24.04
- Debian 11 / 12
- Linux Mint 21+
- Pop!_OS 22.04
- Raspberry Pi OS (arm64)
- TV Boxes com Armbian
