# 🚀 PLAYWAVE - GUIA DE DEPLOY

## 📚 Documentação Disponível

### 🎯 Para Deploy Rápido (5 minutos)
**Arquivo:** `DEPLOY_RAPIDO.md`
- Comandos essenciais
- Deploy em 5 passos
- Troubleshooting rápido

### 📖 Para Deploy Completo (detalhado)
**Arquivo:** `DEPLOY_VPS.md`
- Guia passo a passo completo
- Configuração de backup
- Monitoramento
- Otimizações

### 📤 Para Transferir Projeto
**Arquivo:** `TRANSFERIR_PARA_VPS.md`
- 4 métodos de transferência
- Git, SCP, rsync, FTP
- Exemplos práticos

---

## ⚡ INÍCIO RÁPIDO

### 1. Transferir Projeto
```bash
# Opção A: Via Git (recomendado)
git clone https://github.com/seu-usuario/playwave.git /opt/playwave

# Opção B: Via SCP
scp -r Play-Wave-Aplicativo/ root@2.24.81.194:/opt/playwave/
```

### 2. Configurar Senhas
```bash
cd /opt/playwave
nano docker-compose.production.yml
# Alterar senhas nas linhas: 28, 51, 75, 134, 152
```

### 3. Deploy Automático
```bash
sudo ./deploy-quick.sh
```

### 4. Configurar SSL
```bash
./deploy/init-ssl.sh
```

### 5. Acessar
```
https://playwave.com.br
```

---

## 📋 ARQUIVOS DE DEPLOY

### Scripts Automatizados
- `deploy-quick.sh` - Deploy automático completo
- `deploy/init-ssl.sh` - Configuração SSL (Let's Encrypt)
- `backup.sh` - Backup automático (criar conforme DEPLOY_VPS.md)

### Configurações
- `docker-compose.production.yml` - Stack de produção
- `nginx/nginx.production.conf` - Configuração Nginx
- `backend/Dockerfile` - Build do backend
- `frontend/Dockerfile` - Build do frontend

### Documentação
- `README_DEPLOY.md` - Este arquivo (índice)
- `DEPLOY_RAPIDO.md` - Guia rápido
- `DEPLOY_VPS.md` - Guia completo
- `TRANSFERIR_PARA_VPS.md` - Como transferir projeto

---

## 🎯 INFORMAÇÕES DO SERVIDOR

### Servidor VPS
- **IP:** 2.24.81.194
- **OS:** Ubuntu 20.04+ / Debian 11+
- **RAM:** Mínimo 4GB (recomendado 8GB)
- **CPU:** Mínimo 2 cores (recomendado 4 cores)
- **Disco:** Mínimo 40GB SSD

### Domínio
- **Principal:** playwave.com.br
- **WWW:** www.playwave.com.br
- **DNS:** Apontar para 2.24.81.194

### Portas
- **80** - HTTP (redireciona para HTTPS)
- **443** - HTTPS
- **22** - SSH

---

## 🔐 SENHAS A CONFIGURAR

**⚠️ IMPORTANTE:** Alterar antes do deploy!

### No arquivo `docker-compose.production.yml`:

1. **PostgreSQL** (linha 28)
   ```yaml
   POSTGRES_PASSWORD: 'SuaSenhaForte123!'
   ```

2. **Redis** (linha 51)
   ```yaml
   --requirepass SuaSenhaRedis456!
   ```

3. **RabbitMQ** (linha 75)
   ```yaml
   RABBITMQ_DEFAULT_PASS: SuaSenhaRabbit789!
   ```

4. **Secret Key** (linha 134)
   ```yaml
   SECRET_KEY: "PROD_$(openssl rand -hex 32)"
   ```

5. **Admin** (linha 152)
   ```yaml
   ADMIN_INITIAL_PASSWORD: "Admin@PlayWave2026!"
   ```

---

## 🏗️ ARQUITETURA

### Serviços Docker

```
┌─────────────────────────────────────────┐
│           NGINX (80/443)                │
│         SSL + Reverse Proxy             │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│   FRONTEND     │    │    BACKEND      │
│  (React/Vite)  │    │    (FastAPI)    │
│   Port: 3000   │    │   Port: 8000    │
└────────────────┘    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│   POSTGRES     │  │     REDIS       │  │    RABBITMQ     │
│   Port: 5432   │  │   Port: 6379    │  │   Port: 5672    │
└────────────────┘  └─────────────────┘  └─────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼────────┐                        ┌────────▼────────┐
│ CELERY WORKER  │                        │  CELERY BEAT    │
│  (Background)  │                        │  (Scheduler)    │
└────────────────┘                        └─────────────────┘
```

---

## 📦 ESTRUTURA DO PROJETO

```
/opt/playwave/
├── backend/
│   ├── api/              # Endpoints FastAPI
│   ├── core/             # Models, database, config
│   ├── services/         # Lógica de negócio
│   ├── alembic/          # Migrations
│   ├── uploads/          # Arquivos de usuários
│   ├── Dockerfile        # Build do backend
│   └── requirements.txt  # Dependências Python
│
├── frontend/
│   ├── src/              # Código React
│   ├── public/           # Assets estáticos
│   ├── Dockerfile        # Build do frontend
│   └── package.json      # Dependências Node
│
├── nginx/
│   ├── nginx.production.conf  # Config Nginx
│   └── certbot/               # Certificados SSL
│
├── deploy/
│   ├── init-ssl.sh       # Script SSL
│   └── README.md         # Docs deploy
│
├── docker-compose.production.yml  # Stack produção
├── deploy-quick.sh                # Deploy automático
│
└── docs/
    ├── DEPLOY_RAPIDO.md           # Guia rápido
    ├── DEPLOY_VPS.md              # Guia completo
    ├── TRANSFERIR_PARA_VPS.md     # Como transferir
    └── README_DEPLOY.md           # Este arquivo
```

---

## 🔄 FLUXO DE DEPLOY

```
1. PREPARAR SERVIDOR
   ├── Instalar Docker
   ├── Instalar Docker Compose
   ├── Configurar Firewall
   └── Configurar DNS

2. TRANSFERIR PROJETO
   ├── Via Git (clone)
   ├── Via SCP (upload)
   └── Via rsync (sync)

3. CONFIGURAR
   ├── Alterar senhas
   ├── Verificar domínio
   └── Ajustar variáveis

4. DEPLOY
   ├── Build imagens
   ├── Subir containers
   ├── Executar migrations
   └── Verificar saúde

5. SSL
   ├── Verificar DNS
   ├── Solicitar certificado
   └── Configurar renovação

6. VALIDAR
   ├── Testar backend
   ├── Testar frontend
   ├── Fazer login
   └── Verificar logs

7. MANUTENÇÃO
   ├── Configurar backup
   ├── Configurar monitoramento
   └── Documentar acessos
```

---

## ✅ CHECKLIST DE DEPLOY

### Pré-Deploy
- [ ] Servidor VPS provisionado
- [ ] Docker instalado
- [ ] Docker Compose instalado
- [ ] Firewall configurado (80, 443, 22)
- [ ] DNS configurado (A record → 2.24.81.194)
- [ ] Projeto transferido para `/opt/playwave`

### Configuração
- [ ] Senhas alteradas em `docker-compose.production.yml`
- [ ] Domínio configurado corretamente
- [ ] Scripts com permissão de execução

### Deploy
- [ ] `./deploy-quick.sh` executado com sucesso
- [ ] Todos os containers rodando (status: Up)
- [ ] Migrations executadas
- [ ] Backend respondendo em `/health`

### SSL
- [ ] `./deploy/init-ssl.sh` executado
- [ ] Certificado gerado em `nginx/certbot/conf/`
- [ ] HTTPS funcionando
- [ ] Renovação automática configurada

### Validação
- [ ] Frontend acessível via HTTPS
- [ ] Login funcionando
- [ ] API respondendo
- [ ] Uploads funcionando
- [ ] Logs sem erros críticos

### Pós-Deploy
- [ ] Backup automático configurado
- [ ] Monitoramento configurado
- [ ] Documentação atualizada
- [ ] Credenciais salvas em local seguro

---

## 🆘 SUPORTE

### Problemas Comuns

#### 1. Containers não sobem
```bash
docker-compose -f docker-compose.production.yml logs
df -h  # Verificar espaço
```

#### 2. SSL não funciona
```bash
nslookup playwave.com.br  # Verificar DNS
ls -la nginx/certbot/conf/live/playwave.com.br/
```

#### 3. Backend não conecta
```bash
docker-compose -f docker-compose.production.yml ps postgres
docker-compose -f docker-compose.production.yml logs backend
```

### Comandos Úteis

```bash
# Ver status
docker-compose -f docker-compose.production.yml ps

# Ver logs
docker-compose -f docker-compose.production.yml logs -f

# Reiniciar
docker-compose -f docker-compose.production.yml restart

# Parar
docker-compose -f docker-compose.production.yml stop

# Iniciar
docker-compose -f docker-compose.production.yml start

# Rebuild
docker-compose -f docker-compose.production.yml build --no-cache
docker-compose -f docker-compose.production.yml up -d
```

---

## 📞 CONTATOS

### Acesso ao Servidor
- **IP:** 2.24.81.194
- **Usuário:** root
- **Porta SSH:** 22

### Aplicação
- **URL:** https://playwave.com.br
- **Admin:** admin@playwave.com
- **API:** https://playwave.com.br/api/v1

### Documentação
- **Guia Rápido:** DEPLOY_RAPIDO.md
- **Guia Completo:** DEPLOY_VPS.md
- **Transferência:** TRANSFERIR_PARA_VPS.md

---

## 🎓 RECURSOS ADICIONAIS

### Documentação Técnica
- `AUDITORIA_COMPLETA.md` - Análise do sistema
- `IMPLEMENTACAO_CONCLUIDA.md` - Funcionalidades implementadas
- `TESTES_INTEGRACAO.md` - Roteiros de teste

### Configurações
- `docker-compose.production.yml` - Stack completa
- `nginx/nginx.production.conf` - Configuração Nginx
- `backend/alembic/versions/` - Migrations do banco

---

**Última atualização:** 26 de Maio de 2026  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Deploy
