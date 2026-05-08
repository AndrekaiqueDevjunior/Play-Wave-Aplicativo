# Entidades do Sistema Play Wave

Este documento descreve todas as entidades do sistema de Digital Signage, seus campos, tipos e relacionamentos.

## Sumário

1. [Tenant](#tenant)
2. [User](#user)
3. [Device](#device)
4. [Campaign](#campaign)
5. [Media](#media)
6. [Location](#location)
7. [AudioTrack](#audiotrack)
8. [AudioPlaylist](#audioplaylist)
9. [DevicePairingCode](#devicepairingcode)
10. [DeviceSession](#devicesession)
11. [DeviceEvent](#deviceevent)
12. [PlaybackLog](#playbacklog)
13. [ViewReport](#viewreport)
14. [UserLog](#userlog)

---

## Tenant

Representa uma empresa/cliente no sistema.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| name | String(255) | Nome da empresa cliente | Sim | - |
| plan | Enum | Plano: starter, pro, enterprise | Não | starter |
| is_active | Boolean | Status ativo/inativo | Não | true |
| max_devices | Integer | Número máximo de dispositivos | Não | 10 |
| contact_email | String(255) | Email de contato | Não | - |
| notes | Text | Observações | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Relacionamentos

- **users** (User): Usuários do tenant
- **devices** (Device): Dispositivos do tenant
- **campaigns** (Campaign): Campanhas do tenant
- **media** (Media): Mídias do tenant
- **locations** (Location): Localizações do tenant
- **audio_tracks** (AudioTrack): Faixas de áudio do tenant
- **audio_playlists** (AudioPlaylist): Playlists de áudio do tenant
- **device_events** (DeviceEvent): Eventos de dispositivos
- **playback_logs** (PlaybackLog): Logs de reprodução
- **view_reports** (ViewReport): Relatórios de visualização
- **user_logs** (UserLog): Logs de usuários

---

## User

Representa um usuário do sistema (admin, operador, viewer).

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| name | String(255) | Nome do usuário | Sim | - |
| email | String(255) | Email (único) | Sim | - |
| password_hash | String(255) | Hash da senha | Sim | - |
| role | Enum | Função: admin, operator, viewer | Não | operator |
| is_active | Boolean | Status ativo/inativo | Não | true |
| tenant_id | UUID | ID do tenant | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **UserRole**: admin, operator, viewer

### Relacionamentos

- **tenant** (Tenant): Tenant do usuário

---

## Device

Representa um dispositivo de exibição (TV, tablet, totem, etc.).

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant proprietário | Não | - |
| name | String(255) | Nome do dispositivo | Sim | - |
| pairing_code | String(50) | Código de pareamento (TV-XXXX) | Sim | - |
| device_type | Enum | Tipo: tv, tablet, totem, smartphone, panel, other | Não | tv |
| location | String(255) | Localização do dispositivo | Não | - |
| group | String(255) | Grupo do dispositivo | Não | - |
| status | Enum | Status: waiting_pairing, online, offline, syncing, error, blocked | Não | waiting_pairing |
| is_active | Boolean | Dispositivo ativo | Não | true |
| is_blocked | Boolean | Dispositivo bloqueado pelo admin | Não | false |
| device_token | String(500) | Token seguro de autenticação | Não | - |
| paired_at | DateTime | Data/hora do pareamento | Não | - |
| last_connection | DateTime | Última conexão registrada | Não | - |
| last_seen_at | DateTime | Último heartbeat recebido | Não | - |
| config_version | String(100) | Hash/versão da configuração atual | Não | - |
| current_campaign | String(255) | Nome da campanha atual (cache) | Não | - |
| current_campaign_id | UUID | ID da campanha atual | Não | - |
| audio_playlist_id | UUID | ID da playlist de áudio | Não | - |
| audio_playlist_name | String(255) | Nome da playlist (cache) | Não | - |
| audio_volume | Float | Volume (0.0-1.0) | Não | 0.7 |
| ip_address | String(50) | Endereço IP | Não | - |
| player_version | String(50) | Versão do player | Não | - |
| os | String(50) | Sistema operacional | Não | - |
| storage_used | Integer | Armazenamento usado em MB | Não | 0 |
| notes | Text | Observações | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **DeviceStatus**: waiting_pairing, online, offline, syncing, error, blocked
- **DeviceType**: tv, tablet, totem, smartphone, panel, other

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário
- **campaign** (Campaign): Campanha atual
- **audio_playlist** (AudioPlaylist): Playlist de áudio
- **device_events** (DeviceEvent): Eventos do dispositivo
- **device_sessions** (DeviceSession): Sessões do dispositivo
- **playback_logs** (PlaybackLog): Logs de reprodução
- **view_reports** (ViewReport): Relatórios de visualização

---

## Campaign

Representa uma campanha de mídia.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant proprietário | Não | - |
| name | String(255) | Nome da campanha | Sim | - |
| description | Text | Descrição | Não | - |
| status | Enum | Status: draft, scheduled, active, paused, ended | Não | draft |
| priority | Integer | Prioridade (1=baixa, 10=alta) | Não | 1 |
| start_date | DateTime | Data de início | Não | - |
| end_date | DateTime | Data de término | Não | - |
| device_ids | JSON | Array de IDs de dispositivos | Não | - |
| media_ids | JSON | Array de IDs de mídias | Não | - |
| media_order | JSON | Ordem das mídias com durações | Não | - |
| schedule_all_day | Boolean | Exibir o dia todo | Não | true |
| schedule_days | JSON | Dias da semana | Não | - |
| schedule_start_time | String(10) | Hora de início (HH:MM) | Não | - |
| schedule_end_time | String(10) | Hora de término (HH:MM) | Não | - |
| total_views | Integer | Total de visualizações | Não | 0 |
| target_groups | JSON | Grupos/localizações alvo | Não | - |
| config_version | String(100) | Hash da versão da campanha | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **CampaignStatus**: draft, scheduled, active, paused, ended

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário
- **devices** (Device): Dispositivos da campanha
- **playback_logs** (PlaybackLog): Logs de reprodução
- **view_reports** (ViewReport): Relatórios de visualização

---

## Media

Representa um arquivo de mídia (imagem, vídeo, áudio, URL).

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant proprietário | Não | - |
| name | String(255) | Nome do arquivo/título | Sim | - |
| description | Text | Descrição | Não | - |
| file_url | String(500) | URL do arquivo | Não | - |
| thumbnail_url | String(500) | URL da thumbnail | Não | - |
| type | Enum | Tipo: image, video, audio, external_url | Sim | - |
| mime_type | String(100) | Tipo MIME | Não | - |
| duration | Integer | Duração em segundos | Não | - |
| file_size | Integer | Tamanho em bytes | Não | - |
| resolution | String(50) | Resolução (ex: 1920x1080) | Não | - |
| status | Enum | Status: available, processing, error | Não | available |
| tags | JSON | Array de tags | Não | - |
| notes | Text | Observações | Não | - |
| category | String(100) | Categoria | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **MediaType**: image, video, audio, external_url
- **MediaStatus**: available, processing, error

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário
- **playback_logs** (PlaybackLog): Logs de reprodução
- **view_reports** (ViewReport): Relatórios de visualização

---

## Location

Representa uma localização/grupo de dispositivos.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| name | String(255) | Nome da localização/grupo | Sim | - |
| description | Text | Descrição | Não | - |
| address | String(500) | Endereço | Não | - |
| device_count | Integer | Quantidade de dispositivos | Não | 0 |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário

---

## AudioTrack

Representa uma faixa de áudio para rádio indoor.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| name | String(255) | Nome da faixa | Sim | - |
| description | Text | Descrição | Não | - |
| file_url | String(500) | URL do arquivo | Sim | - |
| mime_type | String(100) | Tipo MIME | Não | - |
| file_size | Integer | Tamanho em bytes | Não | - |
| duration_seconds | Integer | Duração em segundos | Não | - |
| category | Enum | Categoria: music, jingle, announcement, ambient, other | Não | music |
| status | Enum | Status: active, inactive, archived | Não | active |
| notes | Text | Observações | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **AudioTrackCategory**: music, jingle, announcement, ambient, other
- **AudioTrackStatus**: active, inactive, archived

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário

---

## AudioPlaylist

Representa uma playlist de áudio para rádio indoor.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| name | String(255) | Nome da playlist | Sim | - |
| description | Text | Descrição | Não | - |
| status | Enum | Status: active, inactive, archived | Não | active |
| volume_default | Float | Volume padrão (0.0-1.0) | Não | 0.7 |
| loop_enabled | Boolean | Repetir playlist | Não | true |
| shuffle_enabled | Boolean | Embaralhar faixas | Não | false |
| schedule_enabled | Boolean | Agendamento habilitado | Não | false |
| schedule_start_time | String(10) | Hora de início (HH:MM) | Não | - |
| schedule_end_time | String(10) | Hora de término (HH:MM) | Não | - |
| schedule_days | JSON | Dias da semana | Não | - |
| track_ids | JSON | Array de IDs de faixas | Não | - |
| track_volumes | JSON | Volume por faixa (object) | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **AudioPlaylistStatus**: active, inactive, archived

### Relacionamentos

- **tenant** (Tenant): Tenant proprietário
- **devices** (Device): Dispositivos usando a playlist

---

## DevicePairingCode

Representa um código de pareamento para dispositivos.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| code | String(50) | Código de pareamento (ex: TV-A3F9) | Sim | - |
| tenant_id | UUID | ID do tenant que confirmou | Não | - |
| status | Enum | Status: waiting, paired, expired, cancelled | Não | waiting |
| expires_at | DateTime | Expiração (criado_em + 10 min) | Sim | - |
| used_at | DateTime | Data de uso | Não | - |
| device_id | UUID | ID do dispositivo após pareamento | Não | - |
| player_version | String(50) | Versão do player | Não | - |
| os | String(50) | Sistema operacional | Não | - |
| screen_resolution | String(50) | Resolução da tela | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |

### Enums

- **PairingCodeStatus**: waiting, paired, expired, cancelled

### Relacionamentos

- **device** (Device): Dispositivo pareado

---

## DeviceSession

Representa uma sessão de dispositivo com token.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| device_id | UUID | ID do dispositivo | Sim | - |
| tenant_id | UUID | ID do tenant | Não | - |
| token | String(500) | Token de sessão | Sim | - |
| expires_at | DateTime | Expiração do token | Não | - |
| revoked_at | DateTime | Data de revogação | Não | - |
| last_used_at | DateTime | Último uso | Não | - |
| is_active | Boolean | Sessão ativa | Não | true |
| created_at | DateTime | Data de criação | Não | Auto |

### Relacionamentos

- **device** (Device): Dispositivo da sessão

---

## DeviceEvent

Representa eventos de dispositivo (logs, erros, etc.).

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| device_id | UUID | ID do dispositivo | Sim | - |
| device_name | String(255) | Nome do dispositivo | Não | - |
| event_type | Enum | Tipo do evento | Sim | - |
| severity | Enum | Severidade: info, warning, error, critical | Não | info |
| description | Text | Descrição do evento | Não | - |
| metadata | JSON | Dados adicionais (JSON string) | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |

### Enums

- **DeviceEventType**: paired, blocked, unblocked, token_revoked, offline_detected, media_error, network_error, restart, cache_used, playlist_updated, sync
- **EventSeverity**: info, warning, error, critical

### Relacionamentos

- **tenant** (Tenant): Tenant
- **device** (Device): Dispositivo

---

## PlaybackLog

Representa logs de reprodução de mídia.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| device_id | UUID | ID do dispositivo | Sim | - |
| device_name | String(255) | Nome do dispositivo | Não | - |
| campaign_id | UUID | ID da campanha | Sim | - |
| campaign_name | String(255) | Nome da campanha | Não | - |
| media_id | UUID | ID da mídia | Sim | - |
| media_name | String(255) | Nome da mídia | Não | - |
| started_at | DateTime | Início da reprodução | Não | - |
| ended_at | DateTime | Término da reprodução | Não | - |
| duration_ms | Integer | Duração em milissegundos | Não | - |
| status | Enum | Status: completed, interrupted, error | Não | completed |
| created_at | DateTime | Data de criação | Não | Auto |

### Enums

- **PlaybackLogStatus**: completed, interrupted, error

### Relacionamentos

- **tenant** (Tenant): Tenant
- **device** (Device): Dispositivo
- **campaign** (Campaign): Campanha
- **media** (Media): Mídia

---

## ViewReport

Representa relatórios de visualização agregados.

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| tenant_id | UUID | ID do tenant | Não | - |
| device_id | UUID | ID do dispositivo | Sim | - |
| device_name | String(255) | Nome do dispositivo | Não | - |
| campaign_id | UUID | ID da campanha | Sim | - |
| campaign_name | String(255) | Nome da campanha | Não | - |
| media_id | UUID | ID da mídia | Não | - |
| media_name | String(255) | Nome da mídia | Não | - |
| views | Integer | Quantidade de visualizações | Não | 1 |
| date | DateTime | Data do relatório | Não | - |
| status | Enum | Status: success, error, partial | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |
| updated_at | DateTime | Data de atualização | Não | Auto |

### Enums

- **ViewReportStatus**: success, error, partial

### Relacionamentos

- **tenant** (Tenant): Tenant
- **device** (Device): Dispositivo
- **campaign** (Campaign): Campanha
- **media** (Media): Mídia

---

## UserLog

Representa logs de ações de usuários (audit).

### Campos

| Campo | Tipo | Descrição | Obrigatório | Padrão |
|-------|------|-----------|-------------|--------|
| id | UUID | Identificador único | Sim | Auto |
| target_user_id | UUID | ID do usuário afetado | Sim | - |
| target_user_email | String(255) | Email do usuário afetado | Não | - |
| action | Enum | Ação realizada | Sim | - |
| performed_by | String(255) | Email do admin que realizou | Sim | - |
| details | Text | Detalhes adicionais | Não | - |
| tenant_id | UUID | ID do tenant | Não | - |
| created_at | DateTime | Data de criação | Não | Auto |

### Enums

- **UserLogAction**: invite, edit, activate, deactivate, block, unblock, reset_password

### Relacionamentos

- **tenant** (Tenant): Tenant

---

## Diagrama de Relacionamentos

```
Tenant
├── User
├── Device
│   ├── DeviceSession
│   ├── DeviceEvent
│   ├── PlaybackLog
│   └── ViewReport
├── Campaign
│   ├── PlaybackLog
│   └── ViewReport
├── Media
│   ├── PlaybackLog
│   └── ViewReport
├── Location
├── AudioTrack
├── AudioPlaylist
│   └── Device
├── DevicePairingCode
│   └── Device
├── DeviceEvent
├── PlaybackLog
├── ViewReport
└── UserLog
```

## Índices

- **users**: email (unique)
- **devices**: pairing_code (unique), device_token (unique)
- **device_pairing_codes**: code (unique)
- **device_sessions**: token (unique)
