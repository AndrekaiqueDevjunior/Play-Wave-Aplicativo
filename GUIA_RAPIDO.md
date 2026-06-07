# PlayWave — Guia Rápido

Instruções simples para os casos mais comuns.

---

## ⚡ Windows — Instalação Rápida

### 1. Abra PowerShell como Administrador

Pressione `Win + X` → `Windows PowerShell (Admin)`

### 2. Execute o script de instalação

```powershell
cd C:\Users\seu_usuario\Documents\VScode\PlayWave\Play-Wave-Aplicativo
.\scripts\install-windows.ps1
```

### 3. Configure permissões de admin

- Abra Menu Iniciar → Procure "PlayWave"
- Clique direito → Propriedades
- Clique "Avançado..." → Marque "Executar como administrador"
- OK → OK

### 4. Pronto! Execute o PlayWave

Duplo clique no atalho ou pressione `Win` e procure "PlayWave"

---

## 🐳 Docker — Opção Mais Fácil

### 1. Instale Docker

https://www.docker.com/products/docker-desktop

### 2. No diretório do projeto, execute:

```bash
docker-compose up -d
```

### 3. Veja os logs:

```bash
docker logs -f playwave-player
```

### 4. Para parar:

```bash
docker-compose down
```

---

## ⚙️ Configuração Básica

Edite as variáveis de ambiente antes de executar:

**Arquivo: `docker-compose.yml`** (linha ~15)

```yaml
environment:
  VITE_PLAYER_URL: "https://seu-servidor/player"  # ← Altere aqui
```

**Windows**: Edite após instalação em:
```
C:\Users\seu_usuario\AppData\Local\PlayWave\config.json
```

---

## 📋 Comandos Úteis

### Windows

```powershell
# Verificar logs
Get-Content "C:\Users\$env:USERNAME\AppData\Local\PlayWave\logs\main.log" -Tail 50

# Desinstalar
Control Panel → Programs → Programs and Features → PlayWave → Uninstall
```

### Docker

```bash
# Ver status
docker ps -a

# Entrar no container
docker exec -it playwave-player bash

# Ver logs em tempo real
docker logs -f --tail 100 playwave-player

# Reiniciar
docker restart playwave-player

# Remover container
docker-compose down -v
```

---

## 🆘 Problemas Comuns

### "Comando não encontrado" ou "não é reconhecido"

**Windows**: Verifique se o Node.js está instalado
```powershell
node -v
npm -v
```

Se não aparecer, baixe em: https://nodejs.org

### "Connection refused" ao conectar

**Solução**: Verifique a URL do servidor em `VITE_PLAYER_URL`

```bash
# Docker: teste a conectividade
docker exec playwave-player curl https://seu-servidor/api/health
```

### "Permission denied" no Linux/Docker

**Solução**: Aumente as permissões do container

Em `docker-compose.yml`:
```yaml
cap_add:
  - SYS_ADMIN
  - SYS_BOOT
```

### Aplicativo não responde

**Windows**: 
```powershell
# Matar o processo
Stop-Process -Name PlayWave -Force
```

**Docker**:
```bash
docker restart playwave-player
```

---

## 📚 Mais Informações

Para guia completo, veja: **[INSTALACAO_E_USO.md](./INSTALACAO_E_USO.md)**

---

## 🚀 Próximos Passos

1. **Inicie o PlayWave** (Windows ou Docker)
2. **Configure o servidor** na primeira execução
3. **Faça login** com suas credenciais
4. **Envie comandos** via API (minimize, restart, etc)

---

## 💬 Suporte

Dúvidas? Verifique:
- `INSTALACAO_E_USO.md` — Guia completo
- `Dockerfile` — Configuração do container
- `docker-compose.yml` — Orquestração
- Logs (veja "Comandos Úteis" acima)
