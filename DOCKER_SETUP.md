# 🐳 Docker Compose - Play Wave

## 📋 **Visão Geral**

Docker Compose completo para o sistema Play Wave com:
- **PostgreSQL** - Banco de dados principal
- **Redis** - Cache e message broker
- **RabbitMQ** - Message broker avançado
- **Backend** - FastAPI + Celery Worker + Celery Beat
- **Frontend** - React + Nginx

## 🚀 **Comandos Rápidos**

### **Iniciar todos os serviços:**
```bash
docker-compose up -d
```

### **Iniciar com rebuild:**
```bash
docker-compose up -d --build
```

### **Ver logs:**
```bash
docker-compose logs -f
```

### **Parar todos os serviços:**
```bash
docker-compose down
```

### **Remover volumes (cuidado!):**
```bash
docker-compose down -v
```

## 📁 **Estrutura de Serviços**

### 🗄️ **PostgreSQL (playwave-postgres)**
- **Porta:** 5432
- **Banco:** playwave_db
- **Usuário:** postgres
- **Senha:** Kj8#mP2$nL9
- **Volume:** postgres_data

### 🔴 **Redis (playwave-redis)**
- **Porta:** 6379
- **Senha:** R7x$qW9@nB5
- **Volume:** redis_data

### 🐰 **RabbitMQ (playwave-rabbitmq)**
- **Portas:** 5672 (AMQP), 15672 (Management)
- **Usuário:** admin
- **Senha:** F4h&kL8#vG2
- **Volume:** rabbitmq_data
- **Painel:** http://localhost:15672

### 🔧 **Backend (playwave-backend)**
- **Porta:** 8000
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

### 🎵 **Celery Worker (playwave-celery-worker)**
- **Workers:** 4 processos
- **Log:** INFO
- **Tarefas:** Processamento assíncrono

### ⏰ **Celery Beat (playwave-celery-beat)**
- **Agendador:** Tarefas periódicas
- **Log:** INFO

### 🎨 **Frontend (playwave-frontend)**
- **Porta:** 5173
- **URL:** http://localhost:5173
- **Health:** http://localhost:5173/health

## 🔐 **Senhas e Segurança**

### **Banco de Dados:**
- **PostgreSQL:** `Kj8#mP2$nL9`
- **Redis:** `R7x$qW9@nB5`
- **RabbitMQ:** `F4h&kL8#vG2`
- **JWT Secret:** `H9@kL3$mN7#qP5!xR2*wT8$vB6@nJ4`

### **Acesso Externo:**
- **Frontend:** http://localhost:5173
- **API Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **RabbitMQ Management:** http://localhost:15672
  - **Usuário:** admin
  - **Senha:** F4h&kL8#vG2

## 📊 **Volumes Persistentes**

```yaml
volumes:
  postgres_data:    # Dados do PostgreSQL
  redis_data:       # Dados do Redis
  rabbitmq_data:    # Dados do RabbitMQ
```

## 🌐 **Rede Interna**

- **Nome:** playwave-network
- **Subnet:** 172.20.0.0/16
- **Driver:** bridge

## 🔧 **Configurações Especiais**

### **CORS Backend:**
```json
["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173","http://127.0.0.1:3000"]
```

### **Upload de Arquivos:**
- **Tamanho máximo:** 100MB
- **Tipos permitidos:** Imagens, vídeos, áudios
- **Diretório:** ./backend/uploads

### **Rate Limiting:**
- **Requisições/minuto:** 60
- **Burst:** 100

## 🚨 **Health Checks**

Todos os serviços possuem health checks:

```bash
# Verificar status dos serviços
docker-compose ps

# Verificar health checks
docker-compose exec postgres pg_isready -U postgres
docker-compose exec redis redis-cli ping
docker-compose exec rabbitmq rabbitmq-diagnostics ping
docker-compose exec backend curl -f http://localhost:8000/health
```

## 🛠️ **Desenvolvimento vs Produção**

### **Desenvolvimento:**
```bash
# Apenas infraestrutura
docker-compose up -d postgres redis rabbitmq

# Backend local
cd backend && uvicorn main:app --reload

# Frontend local  
cd frontend && npm run dev
```

### **Produção:**
```bash
# Todos os serviços
docker-compose up -d --build
```

## 📝 **Arquivos Importantes**

- `docker-compose.yml` - Configuração principal
- `backend/Dockerfile` - Build do backend
- `frontend/Dockerfile` - Build do frontend
- `frontend/nginx.conf` - Configuração Nginx
- `backend/.env.example` - Template de variáveis

## 🔄 **Comandos Úteis**

### **Recriar serviço específico:**
```bash
docker-compose up -d --force-recreate backend
```

### **Acessar container:**
```bash
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres -d playwave_db
```

### **Ver logs específicos:**
```bash
docker-compose logs -f backend
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### **Backup do banco:**
```bash
docker-compose exec postgres pg_dump -U postgres playwave_db > backup.sql
```

### **Restore do banco:**
```bash
docker-compose exec -T postgres psql -U postgres playwave_db < backup.sql
```

## 🎯 **Primeiro Acesso**

1. **Subir serviços:**
   ```bash
   docker-compose up -d
   ```

2. **Aguardar inicialização:**
   ```bash
   docker-compose logs -f
   ```

3. **Acessar frontend:**
   - URL: http://localhost:5173
   - Login: admin@playwave.com / admin123

4. **Acessar API docs:**
   - URL: http://localhost:8000/docs

5. **Acessar RabbitMQ:**
   - URL: http://localhost:15672
   - Usuário: admin
   - Senha: F4h&kL8#vG2

## ⚡ **Performance**

### **Recursos Recomendados:**
- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Disco:** 50GB+ SSD

### **Otimizações:**
- Redis para cache
- Nginx com gzip
- Build otimizado de frontend
- Workers paralelos no Celery

## 🔒 **Considerações de Segurança**

1. **Senhas fortes** geradas aleatoriamente
2. **Rede isolada** entre containers
3. **Health checks** para monitoramento
4. **CORS restrito** a origens conhecidas
5. **Rate limiting** para proteção
6. **Volumes persistents** com permissões adequadas

## 🚀 **Deploy em Produção**

1. **Alterar senhas** no docker-compose.yml
2. **Configurar domínio** no nginx.conf
3. **Adicionar SSL** (certbot/letsencrypt)
4. **Configurar backup** automático
5. **Monitoramento** externo
6. **Atualizar imagens** regularmente
