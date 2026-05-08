# ESPECIFICAÇÃO TÉCNICA DO BACKEND - PLAY WAVE

## A) RESUMO DO SISTEMA

**Play Wave** é um sistema de **Digital Signage** (sinalização digital) com recursos de **Rádio Indoor**. O sistema permite:

- Gerenciar dispositivos (TVs, totens, tablets) que exibem campanhas de mídia
- Criar campanhas com mídias (imagens, vídeos) e agendar exibição
- Gerenciar biblioteca de mídias com upload de arquivos
- Monitorar dispositivos em tempo real (online/offline/erro)
- Gerenciar playlists de áudio para rádio indoor
- Controle de usuários com roles e permissões
- Relatórios de exibição e analytics
- Multi-tenancy (suporte a múltiplas empresas/tenants)

**Arquitetura Atual do Frontend:**
- Framework: React 18 + Vite
- Router: React Router DOM v6
- State Management: TanStack React Query
- Forms: React Hook Form + Zod
- UI: Radix UI + TailwindCSS
- Backend Atual: Base44 SDK (BaaS)
- Backend Planejado: FastAPI (camada em `src/api/` já definida)

---

## B) LISTA DE MÓDULOS

| Módulo | Descrição | Rotas Principais |
|--------|-----------|------------------|
| **Dashboard** | Visão geral com métricas | `/`, `/dashboard` |
| **Dispositivos** | CRUD de dispositivos, pareamento, monitoramento | `/dispositivos`, `/dispositivos/novo`, `/dispositivos/:id` |
| **Mídias** | Biblioteca de arquivos, upload | `/midias`, `/midias/upload` |
| **Campanhas** | CRUD de campanhas, agendamento, preview | `/campanhas`, `/campanhas/nova`, `/campanhas/:id/preview`, `/campanhas/:id/playlist` |
| **Agenda** | Calendário visual de campanhas | `/agenda` |
| **Monitoramento** | Status em tempo real dos dispositivos | `/monitoramento` |
| **Relatórios** | Analytics, exportação CSV/PDF | `/relatorios` |
| **Localizações** | Grupos de locais para dispositivos | `/localizacoes` |
| **Áudio** | Faixas e playlists sonoras (rádio indoor) | `/audio/faixas`, `/audio/playlists` |
| **Configurações** | Empresa e usuários | `/configuracoes/empresa`, `/configuracoes/usuarios` |
| **Planos** | Gestão de assinatura | `/planos` |
| **Player** | Player de tela (sem layout admin) | `/player` |

---

## C) LISTA DE ENTIDADES

### 1. **Tenant** (Empresa/Cliente)
Multi-tenancy para isolar dados por empresa.

### 2. **User** (Usuários)
Usuários do sistema com roles e permissões.

### 3. **Device** (Dispositivos)
TVs, totens, tablets que exibem conteúdo.

### 4. **DevicePairingCode** (Códigos de Pareamento)
Códigos temporários para vincular novos dispositivos.

### 5. **DeviceSession** (Sessões de Dispositivo)
Sessões ativas de dispositivos conectados.

### 6. **Location** (Localizações)
Grupos de locais (recepção, sala de espera, etc.).

### 7. **Media** (Mídias)
Arquivos de mídia (imagens, vídeos, áudios, URLs externas).

### 8. **Campaign** (Campanhas)
Campanhas de exibição com agendamento.

### 9. **CampaignMediaItem** (Itens de Campanha)
Relacionamento entre campanha e mídia com ordem.

### 10. **AudioTrack** (Faixas de Áudio)
Arquivos MP3 para rádio indoor.

### 11. **AudioPlaylist** (Playlists Sonoras)
Playlists de áudio com configurações de loop/shuffle.

### 12. **PlaybackLog** (Logs de Exibição)
Registro de cada exibição de mídia por dispositivo.

### 13. **DeviceEvent** (Eventos de Dispositivo)
Logs de eventos (erros, conexões, etc.).

### 14. **UserLog** (Logs de Usuário)
Auditoria de ações de usuários.

### 15. **ViewReport** (Relatórios de Visualização)
Relatórios agregados de exibições.

---

## D) DER TEXTUAL (DIAGRAMA ENTIDADE-RELACIONAMENTO)

```
Tenant (1) ----<< (N) User
Tenant (1) ----<< (N) Device
Tenant (1) ----<< (N) Location
Tenant (1) ----<< (N) Campaign
Tenant (1) ----<< (N) Media
Tenant (1) ----<< (N) AudioTrack
Tenant (1) ----<< (N) AudioPlaylist

Location (1) ----<< (N) Device
Device (1) ----<< (N) DevicePairingCode
Device (1) ----<< (N) DeviceSession
Device (1) ----<< (N) PlaybackLog
Device (1) ----<< (N) DeviceEvent
Device (N) ----<< (N) Campaign (muitos-para-muitos via CampaignMediaItem)
Device (1) ----<< (1) AudioPlaylist (rádio indoor)

Campaign (1) ----<< (N) CampaignMediaItem
Media (1) ----<< (N) CampaignMediaItem
Campaign (1) ----<< (N) PlaybackLog

AudioPlaylist (1) ----<< (N) AudioTrack (muitos-para-muitos)

User (1) ----<< (N) UserLog (performed_by)
User (1) ----<< (N) UserLog (target_user_id)

ViewReport (agregado de PlaybackLog)
```

---

## E) TABELA DE ENDPOINTS

### Autenticação

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| POST | `/auth/login` | Login com email/senha | Público |
| POST | `/auth/logout` | Logout | JWT |
| POST | `/auth/refresh` | Refresh token | JWT |
| GET | `/auth/me` | Dados do usuário atual | JWT |
| POST | `/auth/invite` | Convidar usuário | Admin |
| POST | `/auth/reset-password` | Redefinir senha | Público |

### Tenants

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/tenants` | Listar tenants | Superadmin |
| GET | `/tenants/{id}` | Buscar tenant | Admin |
| POST | `/tenants` | Criar tenant | Superadmin |
| PATCH | `/tenants/{id}` | Atualizar tenant | Superadmin |
| DELETE | `/tenants/{id}` | Deletar tenant | Superadmin |
| GET | `/tenants/{id}/stats` | Estatísticas do tenant | Admin |

### Usuários

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/users` | Listar usuários | Admin |
| GET | `/users/{id}` | Buscar usuário | Admin |
| POST | `/users` | Criar usuário | Admin |
| PATCH | `/users/{id}` | Atualizar usuário | Admin |
| DELETE | `/users/{id}` | Deletar usuário | Admin |
| GET | `/users/{id}/logs` | Logs do usuário | Admin |

### Dispositivos

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| POST | `/devices/pair-request` | Solicitar pareamento (device) | Device |
| GET | `/devices/by-code/{code}/status` | Verificar status pareamento | Device |
| POST | `/devices/{id}/pair-confirm` | Confirmar pareamento | Admin |
| GET | `/devices` | Listar dispositivos | Admin |
| GET | `/devices/{id}` | Buscar dispositivo | Admin |
| POST | `/devices` | Criar dispositivo | Admin |
| PATCH | `/devices/{id}` | Atualizar dispositivo | Admin |
| DELETE | `/devices/{id}` | Deletar dispositivo | Admin |
| GET | `/devices/{id}/playlist` | Buscar playlist (device) | Device Token |
| POST | `/devices/{id}/heartbeat` | Enviar heartbeat (device) | Device Token |
| GET | `/devices/{id}/metrics` | Métricas do dispositivo | Admin |
| POST | `/devices/{id}/command` | Enviar comando (restart/sync) | Admin |
| POST | `/devices/{id}/block` | Bloquear dispositivo | Admin |
| POST | `/devices/{id}/unblock` | Desbloquear dispositivo | Admin |
| POST | `/devices/{id}/revoke-token` | Revogar token do dispositivo | Admin |

### Mídias

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/media` | Listar mídias | Admin |
| GET | `/media/{id}` | Buscar mídia | Admin |
| POST | `/media/upload` | Upload de arquivo (multipart) | Admin |
| POST | `/media` | Criar mídia externa (URL) | Admin |
| PATCH | `/media/{id}` | Atualizar mídia | Admin |
| DELETE | `/media/{id}` | Deletar mídia | Admin |
| GET | `/media/{id}/thumbnail` | Buscar thumbnail | Admin |

### Campanhas

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/campaigns` | Listar campanhas | Admin |
| GET | `/campaigns/{id}` | Buscar campanha | Admin |
| POST | `/campaigns` | Criar campanha | Admin |
| PATCH | `/campaigns/{id}` | Atualizar campanha | Admin |
| DELETE | `/campaigns/{id}` | Deletar campanha | Admin |
| POST | `/campaigns/{id}/publish` | Publicar campanha | Admin |
| POST | `/campaigns/{id}/pause` | Pausar campanha | Admin |
| POST | `/campaigns/{id}/resume` | Retomar campanha | Admin |
| GET | `/campaigns/{id}/stats` | Estatísticas da campanha | Admin |

### Localizações

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/locations` | Listar localizações | Admin |
| GET | `/locations/{id}` | Buscar localização | Admin |
| POST | `/locations` | Criar localização | Admin |
| PATCH | `/locations/{id}` | Atualizar localização | Admin |
| DELETE | `/locations/{id}` | Deletar localização | Admin |
| GET | `/locations/{id}/devices` | Dispositivos da localização | Admin |

### Áudio (Rádio Indoor)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/audio/tracks` | Listar faixas | Admin |
| POST | `/audio/tracks/upload` | Upload de faixa (multipart) | Admin |
| PATCH | `/audio/tracks/{id}` | Atualizar faixa | Admin |
| DELETE | `/audio/tracks/{id}` | Deletar faixa | Admin |
| GET | `/audio/playlists` | Listar playlists | Admin |
| GET | `/audio/playlists/{id}` | Buscar playlist | Admin |
| POST | `/audio/playlists` | Criar playlist | Admin |
| PATCH | `/audio/playlists/{id}` | Atualizar playlist | Admin |
| DELETE | `/audio/playlists/{id}` | Deletar playlist | Admin |
| GET | `/audio/devices/{id}/playlist` | Buscar playlist do device | Device Token |

### Relatórios

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/reports/playback` | Logs de playback | Admin |
| GET | `/reports/summary` | Resumo geral | Admin |
| GET | `/reports/device/{id}` | Relatório por dispositivo | Admin |
| GET | `/reports/campaign/{id}` | Relatório por campanha | Admin |
| POST | `/reports/playback` | Registrar exibição (device) | Device Token |
| GET | `/reports/export/csv` | Exportar CSV | Admin |

### Eventos

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/events` | Listar eventos de dispositivo | Admin |

### Sistema

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/health` | Health check | Público |

---

## F) PAYLOADS DE REQUEST/RESPONSE

### Tenant

**POST /tenants**
```json
{
  "name": "Empresa Exemplo",
  "cnpj": "12.345.678/0001-99",
  "contact_email": "contato@empresa.com",
  "plan": "pro",
  "max_devices": 50,
  "primary_color": "#2563eb",
  "logo_url": "https://..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Empresa Exemplo",
  "cnpj": "12.345.678/0001-99",
  "contact_email": "contato@empresa.com",
  "plan": "pro",
  "max_devices": 50,
  "primary_color": "#2563eb",
  "logo_url": "https://...",
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

### User

**POST /users**
```json
{
  "full_name": "João Silva",
  "email": "joao@empresa.com",
  "role": "admin",
  "job_title": "Gerente de Marketing",
  "account_status": "active"
}
```

**Response:**
```json
{
  "id": "uuid",
  "full_name": "João Silva",
  "email": "joao@empresa.com",
  "role": "admin",
  "job_title": "Gerente de Marketing",
  "account_status": "active",
  "last_changed_by": "admin@email.com",
  "last_changed_at": "2026-04-27T10:00:00Z",
  "created_at": "2026-04-27T10:00:00Z"
}
```

### Device

**POST /devices**
```json
{
  "name": "TV Recepção",
  "pairing_code": "TV-4821",
  "device_type": "tv",
  "location": "Recepção",
  "group": "Matriz",
  "os": "Android TV",
  "notes": "",
  "audio_playlist_id": null,
  "audio_volume": 0.7,
  "status": "offline",
  "is_active": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "TV Recepção",
  "pairing_code": "TV-4821",
  "device_type": "tv",
  "location": "Recepção",
  "group": "Matriz",
  "os": "Android TV",
  "notes": "",
  "audio_playlist_id": null,
  "audio_volume": 0.7,
  "status": "offline",
  "is_active": true,
  "current_campaign_id": null,
  "current_campaign": null,
  "device_token": "token-xyz...",
  "last_connection": null,
  "ip_address": null,
  "player_version": null,
  "storage_used": 0,
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

**POST /devices/pair-request (Device)**
```json
{
  "code": "TV-4821",
  "player_version": "3.1.0",
  "os": "Web Player",
  "screen_resolution": "1920x1080"
}
```

**Response:**
```json
{
  "id": "uuid",
  "code": "TV-4821",
  "status": "waiting",
  "expires_at": "2026-04-27T11:00:00Z"
}
```

**POST /devices/{id}/heartbeat (Device)**
```json
{
  "timestamp": "2026-04-27T10:30:00Z",
  "status": "online",
  "ip_address": "192.168.1.101",
  "player_version": "3.1.0",
  "storage_used": 2400,
  "current_media_id": "media-uuid",
  "views_count": 150
}
```

**Response:**
```json
{
  "ok": true,
  "is_blocked": false,
  "config_version": "v1",
  "has_update": false,
  "playlist_updated": false
}
```

### Media

**POST /media/upload (multipart/form-data)**
```
file: <binary>
name: "Banner Promoção.jpg"
type: "image"
description: "Banner de abril"
duration: 10
tags: "promoção, abril"
category: "Promoções"
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Banner Promoção.jpg",
  "type": "image",
  "file_url": "https://storage.example.com/...",
  "thumbnail_url": "https://storage.example.com/thumb-...",
  "file_size": 2400000,
  "duration": 10,
  "mime_type": "image/jpeg",
  "description": "Banner de abril",
  "tags": ["promoção", "abril"],
  "category": "Promoções",
  "status": "available",
  "resolution": "1920x1080",
  "created_at": "2026-04-27T10:00:00Z"
}
```

### Campaign

**POST /campaigns**
```json
{
  "name": "Campanha Abril",
  "description": "Campanha principal do mês",
  "status": "draft",
  "priority": 2,
  "start_date": "2026-04-01",
  "end_date": "2026-04-30",
  "media_ids": ["media-uuid-1", "media-uuid-2"],
  "device_ids": ["device-uuid-1", "device-uuid-2"],
  "schedule_all_day": true,
  "schedule_days": ["seg", "ter", "qua", "qui", "sex", "sab", "dom"],
  "schedule_start_time": "08:00",
  "schedule_end_time": "22:00",
  "target_groups": ["Matriz"],
  "total_views": 0
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Campanha Abril",
  "description": "Campanha principal do mês",
  "status": "draft",
  "priority": 2,
  "start_date": "2026-04-01",
  "end_date": "2026-04-30",
  "media_ids": ["media-uuid-1", "media-uuid-2"],
  "device_ids": ["device-uuid-1", "device-uuid-2"],
  "schedule_all_day": true,
  "schedule_days": ["seg", "ter", "qua", "qui", "sex", "sab", "dom"],
  "schedule_start_time": "08:00",
  "schedule_end_time": "22:00",
  "target_groups": ["Matriz"],
  "total_views": 0,
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

**GET /devices/{id}/playlist (Device)**
```json
{
  "campaign_id": "campaign-uuid",
  "campaign_name": "Campanha Abril",
  "config_version": "v1",
  "media": [
    {
      "id": "media-uuid-1",
      "name": "Banner Promoção.jpg",
      "file_url": "https://...",
      "type": "image",
      "duration": 10
    }
  ]
}
```

### AudioTrack

**POST /audio/tracks/upload (multipart/form-data)**
```
file: <binary MP3>
name: "Música Ambiente 1"
category: "music"
description: "Música suave para recepção"
status: "active"
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Música Ambiente 1",
  "file_url": "https://storage.example.com/...",
  "file_size": 5242880,
  "duration_seconds": 180,
  "mime_type": "audio/mpeg",
  "category": "music",
  "description": "Música suave para recepção",
  "status": "active",
  "created_at": "2026-04-27T10:00:00Z"
}
```

### AudioPlaylist

**POST /audio/playlists**
```json
{
  "name": "Rádio Indoor Loja Centro",
  "description": "Playlist para loja centro",
  "status": "active",
  "volume_default": 0.7,
  "loop_enabled": true,
  "shuffle_enabled": false,
  "track_ids": ["track-uuid-1", "track-uuid-2"]
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Rádio Indoor Loja Centro",
  "description": "Playlist para loja centro",
  "status": "active",
  "volume_default": 0.7,
  "loop_enabled": true,
  "shuffle_enabled": false,
  "track_ids": ["track-uuid-1", "track-uuid-2"],
  "created_at": "2026-04-27T10:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

**GET /audio/devices/{id}/playlist (Device)**
```json
{
  "playlist_id": "playlist-uuid",
  "volume": 0.7,
  "loop": true,
  "shuffle": false,
  "tracks": [
    {
      "id": "track-uuid-1",
      "file_url": "https://...",
      "name": "Música Ambiente 1",
      "duration_seconds": 180
    }
  ]
}
```

### PlaybackLog

**POST /reports/playback (Device)**
```json
{
  "device_id": "device-uuid",
  "campaign_id": "campaign-uuid",
  "media_id": "media-uuid",
  "timestamp": "2026-04-27T10:30:00Z",
  "duration_seconds": 10,
  "status": "success"
}
```

---

## G) REGRAS DE AUTENTICAÇÃO

### Tipos de Autenticação

1. **JWT (Admin/Usuários)**
   - Usado para painel administrativo
   - Header: `Authorization: Bearer <token>`
   - Tokens de acesso (15min) + refresh (7 dias)
   - Armazenado em localStorage no frontend

2. **Device Token (Dispositivos)**
   - Usado para players/tvs
   - Header: `X-Device-Token: <token>`
   - Token permanente gerado no pareamento
   - Cada dispositivo tem seu token único

3. **Pareamento (Pairing Code)**
   - Código temporário (TV-XXXX)
   - Expira em 1 hora
   - Usado apenas para vincular dispositivo

### Fluxo de Autenticação

**Admin/Usuários:**
```
Login → /auth/login → JWT Access + Refresh → /auth/me → Dados do usuário
Refresh → /auth/refresh → Novo Access Token
Logout → /auth/logout → Invalida tokens
```

**Dispositivos:**
```
Pair Request → /devices/pair-request → Código gerado
Polling → /devices/by-code/{code}/status → Aguarda confirmação
Confirm → /devices/{id}/pair-confirm → Device Token gerado
Playlist → /devices/{id}/playlist (X-Device-Token) → Conteúdo
Heartbeat → /devices/{id}/heartbeat (X-Device-Token) → Status
```

---

## H) REGRAS DE AUTORIZAÇÃO

### Roles de Usuário

| Role | Descrição | Permissões |
|------|-----------|-------------|
| **admin** | Administrador completo | CRUD em todos os recursos, gerenciar usuários |
| **user** | Operador | CRUD em campanhas, mídias, dispositivos (não pode gerenciar usuários) |
| **viewer** | Visualizador | Apenas leitura em todos os recursos |

### Permissões por Endpoint

| Recurso | admin | user | viewer |
|---------|-------|------|--------|
| Tenants | CRUD | - | - |
| Usuários | CRUD | - | Leitura |
| Dispositivos | CRUD | CRUD | Leitura |
| Mídias | CRUD | CRUD | Leitura |
| Campanhas | CRUD | CRUD | Leitura |
| Localizações | CRUD | CRUD | Leitura |
| Áudio (Tracks/Playlists) | CRUD | CRUD | Leitura |
| Relatórios | Leitura | Leitura | Leitura |
| Configurações (Empresa) | CRUD | - | - |

### Isolamento por Tenant

- **Todas as queries** devem filtrar por `tenant_id` do usuário autenticado
- **Superadmin** pode acessar todos os tenants
- **Admin/Viewer** acessa apenas seu próprio tenant
- **Device tokens** também são vinculados ao tenant

---

## I) REGRAS DE NEGÓCIO

### Campanhas

1. **Status Lifecycle:**
   - `draft` → `scheduled` → `active` → `paused` → `ended`
   - Campanha só pode ser `active` se tiver mídias e dispositivos vinculados
   - Campanha `ended` não pode ser reativada (criar nova)

2. **Agendamento:**
   - `schedule_all_day: true` → roda 24h
   - `schedule_all_day: false` → respeita `schedule_days`, `schedule_start_time`, `schedule_end_time`
   - Dias da semana: `["seg", "ter", "qua", "qui", "sex", "sab", "dom"]`

3. **Prioridade:**
   - 1 = Baixa, 2 = Normal, 3 = Média, 4 = Alta, 5 = Urgente
   - Usado para ordenação e conflitos de exibição

4. **Publicação:**
   - `POST /campaigns/{id}/publish` → envia para dispositivos vinculados
   - Incrementa `config_version` para forçar refresh nos devices

### Dispositivos

1. **Status:**
   - `online` → heartbeat recebido nos últimos 5 minutos
   - `offline` → sem heartbeat por mais de 5 minutos
   - `syncing` → baixando conteúdo
   - `error` → erro de reprodução/conexão

2. **Pareamento:**
   - Código expira em 1 hora
   - Código único por tenant
   - Após confirmação, gera `device_token` permanente

3. **Ativação:**
   - `is_active: false` → dispositivo não recebe conteúdo mesmo online
   - Usado para desativar temporariamente sem excluir

4. **Rádio Indoor:**
   - `audio_playlist_id` vinculado a dispositivo
   - `audio_volume` (0.0 a 1.0) define volume padrão

### Mídias

1. **Upload:**
   - Máximo 100MB por arquivo
   - Tipos aceitos: `image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `audio/mpeg`, `audio/wav`
   - Gera automaticamente thumbnail para imagens/vídeos

2. **Status:**
   - `processing` → upload em processamento
   - `available` → pronto para uso
   - `archived` → não listado (soft delete)

3. **Duração:**
   - Obrigatório para imagens (segundos de exibição)
   - Automático para vídeos/áudios (extraído do arquivo)

### Áudio (Rádio Indoor)

1. **Faixas:**
   - Máximo 50MB por arquivo MP3
   - Duração extraída automaticamente
   - Categorias: `music`, `jingle`, `announcement`, `ambient`, `other`

2. **Playlists:**
   - `loop_enabled: true` → repete ao terminar
   - `shuffle_enabled: true` → ordem aleatória
   - `volume_default` (0.0 a 1.0) → volume da playlist
   - Ordem das faixas definida pelo array `track_ids`

### Playback e Relatórios

1. **Log de Exibição:**
   - Cada dispositivo envia log ao exibir mídia
   - Inclui: `device_id`, `campaign_id`, `media_id`, `timestamp`, `duration_seconds`, `status`
   - Status: `success`, `partial`, `error`

2. **Agregação:**
   - `total_views` em campanha incrementado via trigger ou background job
   - Relatórios agregados por dia, dispositivo, campanha

### Usuários

1. **Status da Conta:**
   - `active` → pode acessar
   - `inactive` → não pode acessar (mas conta existe)
   - `blocked` → bloqueado por inadimplência (não pode acessar)

2. **Bloqueio:**
   - `blocked_reason` armazena motivo do bloqueio
   - Apenas admin pode desbloquear

3. **Auditoria:**
   - `UserLog` registra todas as ações sensíveis
   - Campos: `target_user_id`, `target_user_email`, `action`, `performed_by`, `details`, `timestamp`

### Multi-tenancy

1. **Isolamento:**
   - Todas as tabelas (exceto auth) têm `tenant_id`
   - Queries sempre filtram por tenant do usuário
   - Foreign keys respeitam tenant

2. **Limite de Dispositivos:**
   - `Tenant.max_devices` define limite
   - Não permite criar dispositivo além do limite

---

## J) PONTOS ONDE O FRONTEND USA MOCK/LOCALSTORAGE

### Mock Data (src/lib/mockData.js)

O frontend usa dados mockados para desenvolvimento quando a API não está configurada:

- `mockDevices` - Lista de dispositivos fictícios
- `mockCampaigns` - Lista de campanhas fictícias
- `mockMedia` - Lista de mídias fictícias
- `mockLocations` - Lista de localizações fictícias
- `mockViewsPerDay` - Dados de gráfico de exibições
- `mockAlerts` - Alertas fictícios

### Base44 SDK (Backend Atual)

O frontend atualmente usa o **Base44 SDK** como backend:

- `src/api/base44Client.js` - Cliente Base44
- `src/lib/AuthContext.jsx` - Autenticação via Base44
- `src/lib/app-params.js` - Parâmetros do app Base44
- Todos os hooks (`UseCampanha.js`, `UseDispositivos.js`, `UseAudio.js`) usam `base44.entities.*`

### Camada FastAPI (Backend Planejado)

Já existe uma camada de API FastAPI planejada em `src/api/`:

- `src/api/http.js` - Cliente HTTP base
- `src/api/campanhas.js` - Endpoints de campanhas
- `src/api/dispositivos.js` - Endpoints de dispositivos
- `src/api/midias.js` - Endpoints de mídias
- `src/api/audio.js` - Endpoints de áudio
- `src/api/localizacoes.js` - Endpoints de localizações
- `src/api/relatorios.js` - Endpoints de relatórios
- `src/api/tenants.js` - Endpoints de tenants

### Fallback Automático

O frontend tem lógica de fallback:

```javascript
// Quando VITE_API_URL não está definido, usa Base44
const BASE_URL = import.meta.env.VITE_API_URL;
if (!BASE_URL) {
  // Usa Base44 SDK
} else {
  // Usa FastAPI via apiFetch
}
```

### localStorage

- `base44_access_token` - Token de acesso Base44
- `base44_app_id` - ID do app
- `base44_functions_version` - Versão das functions

---

## K) ORDEM RECOMENDADA PARA IMPLEMENTAR O BACKEND

### Fase 1: Infraestrutura e Autenticação (Semana 1-2)

1. Setup do projeto FastAPI
2. Configuração de banco de dados (PostgreSQL recomendado)
3. Migrações (Alembic)
4. Implementar autenticação JWT
5. Implementar endpoints de auth (`/auth/login`, `/auth/me`, `/auth/refresh`)
6. Criar middleware de autenticação
7. Criar middleware de multi-tenancy (injeta `tenant_id` no contexto)

### Fase 2: Entidades Básicas (Semana 3)

1. **Tenant** - CRUD completo
2. **User** - CRUD completo com roles
3. **Location** - CRUD completo
4. Testar isolamento por tenant

### Fase 3: Dispositivos e Pareamento (Semana 4)

1. **Device** - CRUD básico
2. **DevicePairingCode** - Sistema de pareamento
3. **DeviceSession** - Sessões ativas
4. Endpoints de pareamento (`/devices/pair-request`, `/devices/by-code/{code}/status`, `/devices/{id}/pair-confirm`)
5. Endpoints de device (`/devices`, `/devices/{id}`)
6. Testar fluxo de pareamento completo

### Fase 4: Mídias e Upload (Semana 5)

1. **Media** - CRUD básico
2. Configurar storage (S3, Azure Blob, ou local)
3. Endpoint `/media/upload` (multipart)
4. Endpoint `/media` (CRUD)
5. Geração de thumbnails (usar Pillow/PIL)
6. Validação de tipos e tamanhos

### Fase 5: Campanhas (Semana 6)

1. **Campaign** - CRUD completo
2. **CampaignMediaItem** - Relacionamento muitos-para-muitos
3. Lógica de agendamento (dias/horários)
4. Endpoint `/campaigns` (CRUD)
5. Endpoint `/campaigns/{id}/publish`
6. Endpoint `/devices/{id}/playlist` (retorna mídias da campanha ativa)

### Fase 6: Player e Heartbeat (Semana 7)

1. Endpoint `/devices/{id}/heartbeat`
2. Lógica de status (online/offline/syncing/error)
3. Atualização de `last_connection`
4. Endpoint `/devices/{id}/command` (restart, sync, clear_cache)
5. Testar player frontend com backend real

### Fase 7: Áudio/Rádio Indoor (Semana 8)

1. **AudioTrack** - CRUD + upload
2. **AudioPlaylist** - CRUD + relacionamento com tracks
3. Endpoint `/audio/tracks` (CRUD + upload)
4. Endpoint `/audio/playlists` (CRUD)
5. Endpoint `/audio/devices/{id}/playlist`
6. Testar rádio indoor no player

### Fase 8: Relatórios e Analytics (Semana 9)

1. **PlaybackLog** - Registro de exibições
2. **DeviceEvent** - Registro de eventos
3. Endpoint `/reports/playback` (POST do device, GET do admin)
4. Endpoint `/reports/summary`
5. Endpoint `/reports/device/{id}`
6. Endpoint `/reports/campaign/{id}`
7. Endpoint `/reports/export/csv`
8. Agregação de dados (background jobs ou triggers)

### Fase 9: Auditoria e Logs (Semana 10)

1. **UserLog** - Registro de ações de usuários
2. Endpoint `/users/{id}/logs`
3. Implementar logging em ações sensíveis
4. Dashboard de logs

### Fase 10: Integração Frontend (Semana 11-12)

1. Configurar `VITE_API_URL` no frontend
2. Substituir chamadas Base44 por chamadas FastAPI gradualmente
3. Testar cada módulo
4. Ajustar payloads se necessário
5. Remover dependência do Base44 SDK
6. Deploy e testes finais

---

## L) CHECKLIST PARA INTEGRAR FRONTEND + BACKEND

### Configuração

- [ ] Definir `VITE_API_URL` no `.env` do frontend
- [ ] Configurar CORS no backend para permitir origem do frontend
- [ ] Configurar storage (S3, Azure, ou local)
- [ ] Configurar variáveis de ambiente do backend (DATABASE_URL, JWT_SECRET, etc.)

### Autenticação

- [ ] Implementar `/auth/login` retornando JWT
- [ ] Implementar `/auth/me` retornando dados do usuário
- [ ] Atualizar `AuthContext.jsx` para usar FastAPI em vez de Base44
- [ ] Remover `base44.auth.me()` e usar `/auth/me`
- [ ] Implementar refresh token

### Dispositivos

- [ ] Implementar `/devices/pair-request`
- [ ] Implementar `/devices/by-code/{code}/status`
- [ ] Implementar `/devices/{id}/pair-confirm`
- [ ] Atualizar `Player.jsx` para usar novos endpoints
- [ ] Testar fluxo de pareamento
- [ ] Implementar `/devices/{id}/heartbeat`
- [ ] Implementar `/devices/{id}/playlist`

### Mídias

- [ ] Implementar `/media/upload` (multipart)
- [ ] Implementar `/media` (CRUD)
- [ ] Atualizar `MediaFormModal.jsx` para usar upload real
- [ ] Atualizar `BibliotecaMidias.jsx` para buscar da API
- [ ] Testar upload de imagens, vídeos e áudios

### Campanhas

- [ ] Implementar `/campaigns` (CRUD)
- [ ] Implementar `/campaigns/{id}/publish`
- [ ] Atualizar `CampaignFormModal.jsx` para salvar na API
- [ ] Atualizar `Campanhas.jsx` para listar da API
- [ ] Atualizar `agenda.jsx` para usar dados reais
- [ ] Testar agendamento e publicação

### Áudio

- [ ] Implementar `/audio/tracks/upload`
- [ ] Implementar `/audio/playlists` (CRUD)
- [ ] Atualizar `AudioTrackFormModal.jsx`
- [ ] Atualizar `AudioPlaylistsFormModal.jsx`
- [ ] Atualizar `FaixasAudio.jsx` e `PlaylistsSonoras.jsx`
- [ ] Testar rádio indoor no player

### Relatórios

- [ ] Implementar `/reports/playback`
- [ ] Implementar `/reports/summary`
- [ ] Atualizar `Relatorios.jsx` para usar dados reais
- [ ] Implementar `/reports/export/csv`
- [ ] Testar exportação

### Outros

- [ ] Implementar `/locations` (CRUD)
- [ ] Atualizar `Localizacoes.jsx`
- [ ] Implementar `/users` (CRUD)
- [ ] Atualizar `ConfigUsuario.jsx`
- [ ] Implementar `/tenants` (CRUD)
- [ ] Atualizar `ConfigEmpresa.jsx`

### Testes Finais

- [ ] Testar fluxo completo: criar mídia → criar campanha → vincular dispositivo → parear → exibir
- [ ] Testar rádio indoor completo
- [ ] Testar relatórios
- [ ] Testar multi-tenancy (criar 2 tenants e verificar isolamento)
- [ ] Testar permissões (admin vs viewer)
- [ ] Testar player com backend real

### Limpeza

- [ ] Remover `src/lib/mockData.js` (ou deixar como fallback)
- [ ] Remover `src/api/base44Client.js` (se não usar mais Base44)
- [ ] Remover hooks que usam Base44 diretamente
- [ ] Atualizar documentação

---

## M) OBSERVAÇÕES ADICIONAIS

### Storage de Arquivos

Recomendações para armazenamento de mídias:

1. **S3 (AWS) ou compatível** - Escalável, CDN integrado
2. **Azure Blob Storage** - Alternativa a S3
3. **MinIO** - Self-hosted, compatível com S3
4. **Local** - Apenas para desenvolvimento

### Banco de Dados

Recomendações:

1. **PostgreSQL** - Recomendado para produção (suporta JSONB, full-text search)
2. **MySQL/MariaDB** - Alternativa viável
3. **SQLite** - Apenas para desenvolvimento

### Background Jobs

Necessário para:

1. Processamento de thumbnails (imagens/vídeos)
2. Agregação de dados de relatórios
3. Limpeza de códigos de pareamento expirados
4. Atualização de status de dispositivos (offline por timeout)

Recomendações:

1. **Celery + Redis** (Python)
2. **FastAPI Background Tasks** (simples)
3. **Temporal** (workflows complexos)

### WebSocket

Opcional para:

1. Atualizações em tempo real no monitoramento
2. Notificações de status de dispositivos
3. Dashboard ao vivo

Se implementar, usar:

1. **FastAPI WebSocket**
2. **Socket.IO** (abstração mais fácil)

### Rate Limiting

Implementar para:

1. `/auth/login` - Prevenir brute force
2. `/devices/pair-request` - Prevenir abuso
3. Upload de arquivos - Limitar por tenant

### Cache

Recomendado para:

1. `/devices/{id}/playlist` - Cache curto (30s)
2. `/campaigns` - Cache médio (5min)
3. `/media` - Cache longo (1h)

Usar:

1. **Redis** - Cache distribuído
2. **Memcached** - Alternativa

---

## N) MODELOS DE BANCO DE DADOS (SQL)

### Tenant

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20),
    contact_email VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'basic',
    max_devices INTEGER DEFAULT 10,
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_tenants_plan ON tenants(plan);
```

### User

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user', -- admin, user, viewer
    job_title VARCHAR(255),
    account_status VARCHAR(20) DEFAULT 'active', -- active, inactive, blocked
    blocked_reason TEXT,
    last_changed_by VARCHAR(255),
    last_changed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### Device

```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    pairing_code VARCHAR(20) UNIQUE,
    device_type VARCHAR(20) DEFAULT 'tv', -- tv, tablet, totem, smartphone, panel, other
    location VARCHAR(255),
    group_name VARCHAR(255),
    os VARCHAR(50),
    notes TEXT,
    audio_playlist_id UUID,
    audio_volume DECIMAL(3,2) DEFAULT 0.7,
    status VARCHAR(20) DEFAULT 'offline', -- online, offline, syncing, error
    is_active BOOLEAN DEFAULT true,
    current_campaign_id UUID,
    device_token VARCHAR(255) UNIQUE,
    last_connection TIMESTAMP,
    ip_address VARCHAR(45),
    player_version VARCHAR(20),
    storage_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_devices_tenant ON devices(tenant_id);
CREATE INDEX idx_devices_pairing_code ON devices(pairing_code);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_device_token ON devices(device_token);
```

### DevicePairingCode

```sql
CREATE TABLE device_pairing_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting', -- waiting, paired, expired
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    player_version VARCHAR(20),
    os VARCHAR(50),
    screen_resolution VARCHAR(20),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_pairing_codes_code ON device_pairing_codes(code);
CREATE INDEX idx_pairing_codes_tenant ON device_pairing_codes(tenant_id);
```

### Media

```sql
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL, -- image, video, audio, external_url
    file_url TEXT NOT NULL,
    thumbnail_url TEXT,
    file_size BIGINT,
    duration INTEGER, -- segundos
    mime_type VARCHAR(100),
    description TEXT,
    tags TEXT[], -- array de strings
    category VARCHAR(100),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'processing', -- processing, available, archived
    resolution VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_media_tenant ON media(tenant_id);
CREATE INDEX idx_media_type ON media(type);
CREATE INDEX idx_media_status ON media(status);
CREATE INDEX idx_media_tags ON media USING GIN(tags);
```

### Campaign

```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft', -- draft, scheduled, active, paused, ended
    priority INTEGER DEFAULT 2, -- 1-5
    start_date DATE,
    end_date DATE,
    schedule_all_day BOOLEAN DEFAULT true,
    schedule_days TEXT[], -- ["seg", "ter", ...]
    schedule_start_time VARCHAR(5) DEFAULT '08:00',
    schedule_end_time VARCHAR(5) DEFAULT '22:00',
    target_groups TEXT[],
    total_views INTEGER DEFAULT 0,
    config_version VARCHAR(20) DEFAULT 'v1',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_campaigns_tenant ON campaigns(tenant_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);
```

### CampaignMediaItem

```sql
CREATE TABLE campaign_media_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    media_id UUID NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(campaign_id, media_id)
);
CREATE INDEX idx_campaign_media_campaign ON campaign_media_items(campaign_id);
CREATE INDEX idx_campaign_media_media ON campaign_media_items(media_id);
```

### AudioTrack

```sql
CREATE TABLE audio_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_size BIGINT,
    duration_seconds INTEGER,
    mime_type VARCHAR(100),
    category VARCHAR(20) DEFAULT 'music', -- music, jingle, announcement, ambient, other
    description TEXT,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, archived
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_audio_tracks_tenant ON audio_tracks(tenant_id);
CREATE INDEX idx_audio_tracks_category ON audio_tracks(category);
```

### AudioPlaylist

```sql
CREATE TABLE audio_playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, archived
    volume_default DECIMAL(3,2) DEFAULT 0.7,
    loop_enabled BOOLEAN DEFAULT true,
    shuffle_enabled BOOLEAN DEFAULT false,
    track_ids UUID[], -- array ordenado de track IDs
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_audio_playlists_tenant ON audio_playlists(tenant_id);
```

### Location

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    address TEXT,
    device_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_locations_tenant ON locations(tenant_id);
```

### PlaybackLog

```sql
CREATE TABLE playback_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    media_id UUID NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'success', -- success, partial, error
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_playback_logs_tenant ON playback_logs(tenant_id);
CREATE INDEX idx_playback_logs_device ON playback_logs(device_id);
CREATE INDEX idx_playback_logs_campaign ON playback_logs(campaign_id);
CREATE INDEX idx_playback_logs_timestamp ON playback_logs(timestamp);
```

### DeviceEvent

```sql
CREATE TABLE device_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- connection, error, sync, command
    severity VARCHAR(20) DEFAULT 'info', -- info, warning, error
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_device_events_tenant ON device_events(tenant_id);
CREATE INDEX idx_device_events_device ON device_events(device_id);
CREATE INDEX idx_device_events_type ON device_events(event_type);
CREATE INDEX idx_device_events_created ON device_events(created_at);
```

### UserLog

```sql
CREATE TABLE user_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    target_user_email VARCHAR(255),
    action VARCHAR(50) NOT NULL, -- invite, edit, delete, activate, deactivate, block, unblock
    performed_by VARCHAR(255) NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_user_logs_tenant ON user_logs(tenant_id);
CREATE INDEX idx_user_logs_target ON user_logs(target_user_id);
CREATE INDEX idx_user_logs_created ON user_logs(created_at);
```

---
