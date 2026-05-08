# Estrutura do Backend Play Wave

## Estrutura Atual Reorganizada

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_migration.py
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       └── auth.py (endpoints de autenticação)
├── core/
│   ├── __init__.py
│   ├── config.py (configurações)
│   ├── database.py (conexão com banco)
│   ├── auth.py (JWT, password hashing)
│   ├── dependencies.py (dependências FastAPI)
│   ├── models.py (modelos SQLAlchemy)
│   └── schemas.py (schemas Pydantic)
├── crud/ (vazio - operações CRUD pendentes)
│   └── __init__.py
├── services/ (vazio - lógica de negócio pendente)
│   └── __init__.py
├── utils/ (vazio - utilitários pendentes)
│   └── __init__.py
├── middleware/ (vazio - middlewares personalizados pendentes)
│   └── __init__.py
├── tasks/ (vazio - tarefas Celery pendentes)
│   └── __init__.py
├── main.py (entry point)
├── init_db.py (script de inicialização)
├── requirements.txt
├── .env.example
└── README.md
```

## Status das Pastas

| Pasta | Status | Descrição |
|-------|--------|-----------|
| **core/** | ✅ Completo | Configurações, banco, autenticação, modelos, schemas |
| **api/v1/** | ⚠️ Parcial | Apenas auth.py implementado |
| **crud/** | ❌ Vazio | CRUDs para todas as entidades pendentes |
| **services/** | ❌ Vazio | Lógica de negócio pendente |
| **utils/** | ❌ Vazio | Utilitários pendentes |
| **middleware/** | ❌ Vazio | Middlewares personalizados pendentes |
| **tasks/** | ❌ Vazio | Tarefas Celery pendentes |

## O que Falta para o Sistema Funcionar

### 1. CRUDs (Operações de Banco)
**Arquivos a criar em `crud/`:**
- `crud/tenant.py` - CRUD para Tenant
- `crud/user.py` - CRUD para User
- `crud/device.py` - CRUD para Device
- `crud/campaign.py` - CRUD para Campaign
- `crud/media.py` - CRUD para Media
- `crud/location.py` - CRUD para Location
- `crud/audio_track.py` - CRUD para AudioTrack
- `crud/audio_playlist.py` - CRUD para AudioPlaylist
- `crud/device_pairing_code.py` - CRUD para DevicePairingCode
- `crud/device_session.py` - CRUD para DeviceSession
- `crud/device_event.py` - CRUD para DeviceEvent
- `crud/playback_log.py` - CRUD para PlaybackLog
- `crud/view_report.py` - CRUD para ViewReport
- `crud/user_log.py` - CRUD para UserLog

### 2. Schemas Pydantic
**Atualizar `core/schemas.py` ou criar módulos separados:**
- Schemas para todas as 14 entidades
- Schemas de criação (Create)
- Schemas de atualização (Update)
- Schemas de resposta (Response)

### 3. Endpoints API
**Arquivos a criar em `api/v1/`:**
- `api/v1/tenants.py` - Endpoints para Tenant
- `api/v1/users.py` - Endpoints para User
- `api/v1/devices.py` - Endpoints para Device
- `api/v1/campaigns.py` - Endpoints para Campaign
- `api/v1/media.py` - Endpoints para Media
- `api/v1/locations.py` - Endpoints para Location
- `api/v1/audio/tracks.py` - Endpoints para AudioTrack
- `api/v1/audio/playlists.py` - Endpoints para AudioPlaylist
- `api/v1/device/pairing.py` - Endpoints para pareamento
- `api/v1/reports.py` - Endpoints para relatórios

### 4. Serviços de Negócio
**Arquivos a criar em `services/`:**
- `services/device_service.py` - Lógica de pareamento, heartbeat, sincronização
- `services/campaign_service.py` - Lógica de agendamento, distribuição
- `services/report_service.py` - Lógica de geração de relatórios
- `services/notification_service.py` - Envio de notificações (opcional)

### 5. Utilitários
**Arquivos a criar em `utils/`:**
- `utils/security.py` - Funções de segurança adicionais
- `utils/validators.py` - Validadores customizados
- `utils/helpers.py` - Funções auxiliares

### 6. Middlewares
**Arquivos a criar em `middleware/`:**
- `middleware/rate_limit.py` - Rate limiting
- `middleware/logging.py` - Logging de requisições
- `middleware/tenant.py` - Middleware de multi-tenancy

### 7. Tarefas Celery
**Arquivos a criar em `tasks/`:**
- `tasks/celery_app.py` - Configuração do Celery
- `tasks/sync_tasks.py` - Tarefas de sincronização
- `tasks/report_tasks.py` - Tarefas de relatórios agendados
- `tasks/notification_tasks.py` - Tarefas de notificações

## Prioridade de Implementação

1. **Alta Prioridade** (Sistema básico funcional):
   - CRUDs para Device, Campaign, Media
   - Schemas Pydantic completos
   - Endpoints API básicos (CRUD)
   - Atualizar `main.py` para incluir novos routers

2. **Média Prioridade** (Funcionalidades avançadas):
   - Serviços de negócio
   - Endpoints de relatórios
   - Middleware de multi-tenancy

3. **Baixa Prioridade** (Otimizações):
   - Tarefas Celery
   - Rate limiting
   - Logging avançado

## Próximos Passos Sugeridos

1. Criar schemas Pydantic para todas as entidades
2. Criar CRUDs básicos (get, create, update, delete)
3. Criar endpoints API para Device, Campaign, Media
4. Testar fluxo completo com frontend
5. Implementar serviços de negócio
6. Adicionar tarefas Celery para processamento assíncrono
