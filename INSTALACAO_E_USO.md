# PlayWave — Guia de Instalação e Uso

Este guia cobre instalação do executável Windows (.exe), uso do aplicativo e geração via Docker.

---

## 📦 Instalação no Windows

### Pré-requisitos

- Windows 10 ou superior
- Acesso administrador (para comandos de shutdown/restart)
- Conexão com internet

### Passo 1: Obter o Instalador

O instalador está em `frontend/electron/dist-electron/PlayWave-*.exe`

Se ainda não tiver o build:

```powershell
cd frontend/electron
npm install
npm run build           # Constrói o bundle do Vite
npm run electron:build  # Gera o .exe
```

Saída: `frontend/electron/dist-electron/PlayWave-x.x.x.exe`

### Passo 2: Instalar o Aplicativo

1. **Duplo clique** no arquivo `.exe`
2. Siga o assistente (selecione pasta de instalação)
3. Aguarde conclusão
4. O aplicativo será adicionado ao Menu Iniciar

### Passo 3: Configurar Permissões de Administrador

Para que os comandos de **shutdown/restart/show_desktop** funcionem, o PlayWave precisa rodar como **Administrador**.

#### Opção A: Criar Atalho com Permissão Elevada

1. Localize o atalho do PlayWave no Menu Iniciar
2. Clique com botão direito → "Abrir localização do arquivo"
3. Clique com botão direito no atalho → **Propriedades**
4. Clique em **"Avançado..."**
5. Marque **"Executar como administrador"**
6. Clique **OK** → **OK**

#### Opção B: Sempre Executar como Admin (sem prompt)

```powershell
# Execute como Administrador no PowerShell:
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut(
  "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\PlayWave.lnk"
)
$shortcut.TargetPath = "C:\Program Files\PlayWave\PlayWave.exe"
# A propriedade de admin geralmente é aplicada via sistema de arquivos
```

---

## 🚀 Uso do Aplicativo

### Primeira Execução

1. Abra o **PlayWave**
2. Selecione seu servidor (URL da API)
3. Faça login com suas credenciais
4. O aplicativo entra em modo **Kiosk** (tela cheia, sem interface de janela padrão)

### Comandos Disponíveis (via Admin)

Você pode enviar comandos para o dispositivo via API:

| Comando | Ação | Parâmetros |
|---------|------|-----------|
| `minimize_window` | Minimiza a janela | — |
| `restore_window` | Restaura a janela | — |
| `show_desktop` | Minimiza e auto-restaura | `duration_seconds` (1-300s) |
| `restart_app` | Reinicia o PlayWave | — |
| `restart_device` | Reinicia o Windows | Requer admin |
| `shutdown_device` | Desliga o Windows | Requer admin |

### Exemplo: Enviar Comando via API

```bash
curl -X POST "https://seu-servidor/api/v1/devices/{device_id}/commands" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command_type": "show_desktop",
    "payload": {
      "duration_seconds": 10
    }
  }'
```

### Logs e Troubleshooting

Logs do aplicativo:
- **Windows**: `C:\Users\{seu_usuario}\AppData\Local\PlayWave\logs\main.log`

Abra esta pasta para verificar erros de conexão ou execução de comandos.

---

## 🐳 Geração e Uso via Docker

### Pré-requisitos

- Docker instalado
- Conexão com internet
- Espaço em disco (~2GB)

### Passo 1: Criar Dockerfile

Crie um arquivo `Dockerfile` na raiz do projeto:

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar dependências do backend (se necessário)
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Instalar e buildar frontend
WORKDIR /app/frontend/electron
RUN npm install
RUN npm run build
RUN npm run electron:build:linux  # Build para Linux (em Docker)

# Runtime stage
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libnotify4 \
    libgconf-2-4 \
    libappindicator1 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    xdg-utils \
    libasound2 \
    libxext6 \
    libxrandr2 \
    libgbm1 \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório do app
WORKDIR /app

# Copiar build do frontend
COPY --from=builder /app/frontend/electron/dist-electron/ ./

# Expor porta (se necessário)
EXPOSE 5173

# Definir variáveis de ambiente
ENV DISPLAY=:0
ENV VITE_PLAYER_URL=http://localhost:3000/player

# Executar aplicativo
CMD ["./PlayWave"]
```

### Passo 2: Build da Imagem Docker

```bash
# Na raiz do projeto
docker build -t playwave:latest .
```

### Passo 3: Executar o Container

#### Opção A: Container Interativo (Debug)

```bash
docker run -it \
  --name playwave-player \
  -e VITE_PLAYER_URL="https://seu-servidor/player" \
  -v ~/.config/PlayWave:/root/.config/PlayWave \
  playwave:latest
```

#### Opção B: Container em Background (Produção)

```bash
docker run -d \
  --name playwave-player \
  --restart unless-stopped \
  -e VITE_PLAYER_URL="https://seu-servidor/player" \
  -v ~/.config/PlayWave:/root/.config/PlayWave \
  -v /var/log/playwave:/app/logs \
  playwave:latest
```

#### Opção C: Docker Compose (Recomendado)

Crie `docker-compose.yml`:

```yaml
version: '3.8'

services:
  playwave:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: playwave-player
    restart: unless-stopped
    environment:
      VITE_PLAYER_URL: "https://seu-servidor/player"
      DISPLAY: ":0"
      NODE_ENV: "production"
    volumes:
      - ~/.config/PlayWave:/root/.config/PlayWave
      - ./logs:/app/logs
    networks:
      - playwave
    # Opcional: para acesso a dispositivos especiais (som, USB, etc)
    # devices:
    #   - /dev/dri:/dev/dri
    #   - /dev/snd:/dev/snd

networks:
  playwave:
    driver: bridge
```

**Executar:**

```bash
docker-compose up -d
```

---

## 📋 Configuração do PlayWave

### Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `VITE_PLAYER_URL` | URL do servidor backend | `https://api.playwave.com.br/player` |
| `PLAYER_KIOSK` | Forçar modo kiosk (dev) | `true` / `false` |
| `NODE_ENV` | Ambiente | `development` / `production` |
| `DISPLAY` | Display X11 (Linux) | `:0` |

### Arquivo de Configuração

Arquivo: `~/.config/PlayWave/config.json` (após primeira execução)

```json
{
  "api_url": "https://seu-servidor",
  "device_id": "auto-gerado",
  "kiosk_mode": true,
  "language": "pt-BR"
}
```

---

## 🔍 Troubleshooting

### "Command not found" no Docker

**Problema**: O executável não foi gerado corretamente.

**Solução**:
```bash
docker run -it playwave:latest ls -la /app
```

Verifique se o arquivo `PlayWave` está em `/app`.

### "Connection refused" ao conectar com backend

**Problema**: URL do servidor errada ou backend offline.

**Solução**:
```bash
# Dentro do container:
docker exec playwave-player curl -v https://seu-servidor/api/health
```

Verifique a conectividade de rede.

### Permissões negadas para shutdown (Linux)

**Problema**: Container tenta executar `shutdown` sem privilégios.

**Solução**: Adicione ao docker-compose ou `docker run`:

```yaml
cap_add:
  - SYS_ADMIN
  - SYS_BOOT
security_opt:
  - apparmor=unconfined
```

Ou execute como `root`:

```bash
docker run --user root ... playwave:latest
```

---

## 📊 Monitoramento

### Ver Logs do Container

```bash
docker logs -f playwave-player
```

### Ver Logs Locais (Windows)

```powershell
Get-Content "C:\Users\$env:USERNAME\AppData\Local\PlayWave\logs\main.log" -Tail 50
```

### Health Check

```bash
docker exec playwave-player curl http://localhost:5173/health
```

---

## 🔒 Segurança

### Recomendações para Produção

1. **Rode como usuário não-root** (Docker):
   ```dockerfile
   RUN useradd -m -s /bin/bash playwave
   USER playwave
   ```

2. **Limite recursos**:
   ```yaml
   # docker-compose.yml
   resources:
     limits:
       cpus: '2'
       memory: 1G
   ```

3. **Use volumes read-only** para arquivos imutáveis:
   ```bash
   -v /path/to/assets:/app/assets:ro
   ```

4. **Ative o modo kiosk** (impede acesso ao desktop):
   ```bash
   -e PLAYER_KIOSK=true
   ```

---

## 📝 Suporte

Para problemas ou dúvidas:
- Abra uma issue em: https://github.com/seu-repo/issues
- Contate: support@playwave.com.br
