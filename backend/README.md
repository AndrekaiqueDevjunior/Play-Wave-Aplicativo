# Play Wave Backend

Backend em FastAPI para o sistema de Digital Signage.

## Dependências Externas

Antes de iniciar, certifique-se de ter instalado:

- **PostgreSQL** (versão 14+)
- **Redis** (versão 6+)
- **RabbitMQ** (versão 3.12+)

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

O arquivo `.env` já contém senhas aleatórias geradas. Para produção, altere as senhas conforme necessário.

### Variáveis de Ambiente

```env
# Database (PostgreSQL)
DATABASE_URL=postgresql://playwave:Z7xK9mP2qR8nV4wY@localhost:5432/playwave

# JWT
SECRET_KEY=J8mN3pQ5rT7vW2xZ9kL4sD6fG1hB8cE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=R4hM7pQ2tW8xY5zK9vL3nD6fG1bB8cE

# RabbitMQ
RABBITMQ_URL=amqp://playwave:T5nK8pQ3vR7xY2wZ9mL4sD6fG1hB8cE@localhost:5672/playwave
RABBITMQ_USER=playwave
RABBITMQ_PASSWORD=T5nK8pQ3vR7xY2wZ9mL4sD6fG1hB8cE

# Celery
CELERY_BROKER_URL=amqp://playwave:T5nK8pQ3vR7xY2wZ9mL4sD6fG1hB8cE@localhost:5672/playwave
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Iniciar Serviços

#### PostgreSQL

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE playwave;
CREATE USER playwave WITH PASSWORD 'Z7xK9mP2qR8nV4wY';
GRANT ALL PRIVILEGES ON DATABASE playwave TO playwave;
\q
```

#### Redis

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis-server

# Configurar senha (opcional)
sudo nano /etc/redis/redis.conf
# Adicionar: requirepass R4hM7pQ2tW8xY5zK9vL3nD6fG1bB8cE
sudo systemctl restart redis-server
```

#### RabbitMQ

```bash
# Linux (Ubuntu/Debian)
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server

# Criar usuário e vhost
sudo rabbitmqctl add_user playwave T5nK8pQ3vR7xY2wZ9mL4sD6fG1hB8cE
sudo rabbitmqctl add_vhost playwave
sudo rabbitmqctl set_permissions -p playwave playwave ".*" ".*" ".*"
```

## Inicializar Banco de Dados

```bash
python init_db.py
```

Isso criará as tabelas e os usuários iniciais:
- **Admin**: admin@playwave.com / admin123
- **Operador**: operador@playwave.com / operador123

## Executar o Servidor

```bash
uvicorn main:app --reload
```

A API estará disponível em `http://localhost:8000`

## Executar Worker Celery (opcional)

```bash
celery -A main.celery worker --loglevel=info
```

## Documentação da API

Acesse `http://localhost:8000/docs` para ver a documentação interativa do Swagger.

## Endpoints de Autenticação

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@playwave.com",
  "password": "admin123"
}
```

### Obter Usuário Atual
```bash
GET /api/auth/me
Authorization: Bearer <token>
```

### Logout
```bash
POST /api/auth/logout
Authorization: Bearer <token>
```

## Migrações

Para criar uma nova migração:

```bash
alembic revision --autogenerate -m "descrição da migração"
```

Para aplicar as migrações:

```bash
alembic upgrade head
```
