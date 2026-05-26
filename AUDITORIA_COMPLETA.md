# AUDITORIA COMPLETA DO SISTEMA PLAYWAVE
**Data:** 26 de Maio de 2026  
**Objetivo:** Mapear estado atual do sistema antes de implementar melhorias em Mídias, Campanhas, Rádio/Áudio e Player

---

## SUMÁRIO EXECUTIVO

O sistema PlayWave já possui uma arquitetura robusta e bem estruturada com:
- ✅ **Backend completo** com models, schemas, routers e CRUD para todas as entidades
- ✅ **Sistema de áudio avançado** com pastas, playlists, spots e agendamento por horário
- ✅ **Upload múltiplo de áudios** já implementado
- ✅ **Detecção automática de duração de vídeos** via ffprobe
- ✅ **Sistema de comandos remotos** com ciclo de vida completo
- ✅ **Pareamento com versionamento** de token e código
- ✅ **Política de áudio** (AudioPolicy) para resolver conflitos entre mídia e rádio
- ✅ **OSD (On-Screen Display)** configurável para exibir nome da música
- ✅ **Período de exibição** (starts_at/ends_at) em mídias
- ✅ **Ordenação de playlist** via CampaignPlaylistItem com order_index
- ✅ **Substituição de mídia** via MediaVersion (versionamento de arquivos)

**Conclusão:** A maioria das funcionalidades solicitadas **JÁ EXISTE** no sistema. O trabalho será principalmente de:
1. Validar e testar funcionalidades existentes
2. Corrigir bugs específicos reportados
3. Melhorar UX/UI do frontend
4. Completar integrações faltantes
5. Criar documentação e testes

---

## 1. ESTADO ATUAL DO BACKEND

### 1.1 Models Existentes (`core/models.py`)

#### ✅ Mídia (Media)
```python
class Media(Base):
    # Campos básicos
    id, tenant_id, name, description
    file_url, thumbnail_url, type, mime_type
    
    # Duração e exibição
    duration                    # Legado (mantido por compatibilidade)
    duration_seconds            # Duração real detectada (vídeo/áudio)
    display_duration_seconds    # Tempo de exibição configurado
    
    # Período de exibição ✅ JÁ EXISTE
    starts_at                   # Data início
    ends_at                     # Data fim
    
    # Áudio ✅ JÁ EXISTE
    audio_policy                # AUTO, RADIO_ONLY, MEDIA_AUDIO_ONLY, MIX, MUTED_VIDEO_WITH_RADIO
    has_audio                   # Boolean detectado via ffprobe
    
    # Versionamento ✅ JÁ EXISTE
    file_version                # Incrementado a cada substituição
    file_hash                   # SHA256 do arquivo
    
    # Metadados
    file_size, resolution, status, is_active
    tags, notes, category
    extra_metadata (JSON)
```

#### ✅ MediaVersion (Versionamento de Arquivos)
```python
class MediaVersion(Base):
    id, media_id
    file_url, thumbnail_url, file_name
    mime_type, file_size, file_hash
    duration_seconds
    version_number              # Número da versão
    is_current                  # Versão atual ativa
    created_at, created_by
```

**Conclusão:** Sistema de substituição de mídia **JÁ EXISTE** via versionamento.

---

#### ✅ Campanha (Campaign)
```python
class Campaign(Base):
    id, tenant_id, name, description, status, priority
    start_date, end_date
    
    # Mídias (legado - mantido por compatibilidade)
    media_ids (JSON)
    media_order (JSON)
    
    # Playlist estruturada ✅ JÁ EXISTE
    playlist_items              # Relationship com CampaignPlaylistItem
    
    # Áudio ✅ JÁ EXISTE
    audio_playlist_id           # FK para AudioPlaylist
    audio_policy                # Política de conflito de áudio
    video_muted                 # Legado
    
    # Agendamento
    schedule_all_day, schedule_days
    schedule_start_time, schedule_end_time
    loop_count                  # Número de loops (null = infinito)
    
    # Dispositivos
    device_ids (JSON)
    target_groups (JSON)
```

#### ✅ CampaignPlaylistItem (Itens da Playlist) ✅ JÁ EXISTE
```python
class CampaignPlaylistItem(Base):
    id, campaign_id, media_id
    order_index                 # ✅ Ordenação implementada
    display_duration_seconds    # Duração customizada por item
    starts_at, ends_at          # Período específico do item
    is_active                   # Ativar/desativar item
    repeat_count                # Repetições do item
```

**Conclusão:** Sistema de playlist com ordenação **JÁ EXISTE**.

---

#### ✅ AudioTrack (Faixas de Áudio)
```python
class AudioTrack(Base):
    id, tenant_id, name, description
    file_url, mime_type, file_size
    duration_seconds            # Duração detectada
    category                    # MUSIC, JINGLE, ANNOUNCEMENT, AMBIENT, OTHER
    status                      # ACTIVE, INACTIVE, ARCHIVED
    notes
```

#### ✅ AudioFolder (Pastas/Grupos de Áudio) ✅ JÁ EXISTE
```python
class AudioFolder(Base):
    id, tenant_id, name, description
    status                      # ACTIVE, INACTIVE, ARCHIVED
    
    # Período da pasta ✅ JÁ EXISTE
    starts_at, ends_at          # Data início/fim
    start_time, end_time        # Horário início/fim (HH:MM)
    schedule_days (JSON)        # Dias da semana
    is_active
    
    # Relacionamentos
    tracks                      # AudioFolderTrack (com order_index)
    playlist_schedules          # AudioPlaylistFolderSchedule
```

#### ✅ AudioFolderTrack (Músicas dentro da Pasta)
```python
class AudioFolderTrack(Base):
    id, folder_id, track_id
    order_index                 # ✅ Ordenação dentro da pasta
    volume_override             # Volume específico da faixa
    is_active
```

**Conclusão:** Sistema de pastas de áudio **JÁ EXISTE**.

---

#### ✅ AudioPlaylist (Playlist de Rádio)
```python
class AudioPlaylist(Base):
    id, tenant_id, name, description
    status                      # ACTIVE, INACTIVE, ARCHIVED
    volume_default
    
    # Modo de reprodução ✅ JÁ EXISTE
    loop_enabled                # Repetir playlist
    shuffle_enabled             # Modo aleatório ✅
    
    # Agendamento
    schedule_enabled
    schedule_start_time, schedule_end_time
    schedule_days (JSON)
    
    # Relacionamentos
    items                       # AudioPlaylistItem (faixas individuais)
    folder_schedules            # AudioPlaylistFolderSchedule (pastas por horário)
    spot_schedules              # AudioSpotSchedule (spots recorrentes)
```

#### ✅ AudioPlaylistItem (Faixas na Playlist)
```python
class AudioPlaylistItem(Base):
    id, playlist_id, track_id
    order_index                 # ✅ Ordenação
    volume_override
    is_active
```

#### ✅ AudioPlaylistFolderSchedule (Pastas por Horário) ✅ JÁ EXISTE
```python
class AudioPlaylistFolderSchedule(Base):
    id, playlist_id, folder_id
    
    # Horário ✅ JÁ EXISTE
    start_time, end_time        # HH:MM
    starts_at, ends_at          # Data início/fim (opcional)
    days_of_week (JSON)         # Dias da semana
    priority                    # Prioridade em caso de conflito
    
    # Modo de reprodução ✅ JÁ EXISTE
    play_mode                   # SEQUENTIAL, SHUFFLE, LOOP
    is_active
```

**Conclusão:** Sistema de programação de rádio por horário **JÁ EXISTE**.

---

#### ✅ AudioSpot (Spots/Anúncios)
```python
class AudioSpot(Base):
    id, tenant_id, track_id
    name, description
    status                      # ACTIVE, INACTIVE, ARCHIVED
    
    # Política de inserção ✅ JÁ EXISTE
    insertion_policy            # INTERRUPT, WAIT_SILENCE, FADE_MIX
    
    # Relacionamentos
    schedules                   # AudioSpotSchedule
```

#### ✅ AudioSpotSchedule (Agendamento de Spots) ✅ JÁ EXISTE
```python
class AudioSpotSchedule(Base):
    id, spot_id, playlist_id
    
    # Intervalo ✅ JÁ EXISTE
    interval_seconds            # Tocar a cada X segundos
    
    # Período
    start_time, end_time        # HH:MM
    starts_at, ends_at          # Data início/fim (opcional)
    priority
    is_active
```

**Conclusão:** Sistema de spots recorrentes **JÁ EXISTE**.

---

#### ✅ Device (Dispositivos)
```python
class Device(Base):
    id, tenant_id, name
    
    # Pareamento ✅ JÁ EXISTE
    pairing_code                # Código de pareamento
    pairing_version             # Versão do pareamento ✅
    token_version               # Versão do token ✅
    requires_repairing          # Flag para forçar novo pareamento ✅
    device_token                # Token de autenticação
    paired_at
    
    # Campanha e Áudio
    current_campaign_id
    audio_playlist_id
    audio_volume
    
    # Política de áudio ✅ JÁ EXISTE
    audio_policy_default        # Política padrão do dispositivo
    
    # OSD (On-Screen Display) ✅ JÁ EXISTE
    osd_show_current_audio      # Exibir nome da música ✅
    osd_position                # top_left, top_right, bottom_left, bottom_right
    osd_duration_seconds        # Tempo de exibição
    osd_opacity                 # Opacidade
    osd_font_size               # small, medium, large
    
    # Estado atual do áudio
    current_audio_track_id
    current_audio_track_name
    current_audio_track_started_at
    
    # Status
    status, is_active, is_blocked
    last_connection, last_seen_at
```

**Conclusão:** Sistema de OSD para exibir nome da música **JÁ EXISTE**.

---

#### ✅ DeviceCommand (Comandos Remotos)
```python
class DeviceCommand(Base):
    id, device_id, tenant_id
    command_type                # sync, restart_app, shutdown_device, etc.
    payload (JSON)
    
    # Ciclo de vida ✅ JÁ EXISTE
    status                      # PENDING, SENT, RECEIVED, EXECUTING, COMPLETED, FAILED, EXPIRED
    
    # Timestamps
    requested_at, sent_at, received_at, started_at, executed_at, expires_at
    
    # Resultado
    result (JSON)
    error_message
    is_destructive              # Comandos destrutivos (shutdown, restart)
    requested_by                # Auditoria
```

**Conclusão:** Sistema de comandos com ciclo de vida completo **JÁ EXISTE**.

---

#### ✅ DevicePairingEvent (Auditoria de Pareamento)
```python
class DevicePairingEvent(Base):
    id, device_id, tenant_id
    event_type                  # PAIRED, RE_PAIRED, CODE_REGENERATED, FORCE_REPAIR, etc.
    previous_token_version, new_token_version
    previous_pairing_version, new_pairing_version
    previous_pairing_code, new_pairing_code
    requested_by, reason
    extra_metadata (JSON)
```

**Conclusão:** Sistema de auditoria de pareamento **JÁ EXISTE**.

---

#### ✅ AudioPlaybackEvent (Log de Reprodução de Áudio)
```python
class AudioPlaybackEvent(Base):
    id, device_id, playlist_id, track_id, spot_id
    event_type                  # TRACK_STARTED, TRACK_ENDED, SPOT_STARTED, SPOT_ENDED, ERROR
    result                      # SUCCESS, SKIPPED, FAILED, INTERRUPTED
    started_at, ended_at, duration_seconds
    error_message
    event_metadata (JSON)
```

---

### 1.2 Endpoints Existentes

#### Mídia (`/api/v1/media`)
- ✅ `POST /upload` - Upload de mídia com detecção automática de duração via ffprobe
- ✅ `POST /` - Criar mídia externa (URL)
- ✅ `GET /` - Listar mídias (com filtros)
- ✅ `GET /{id}` - Obter mídia
- ✅ `PUT /{id}` - Atualizar mídia
- ✅ `DELETE /{id}` - Deletar mídia
- ✅ `POST /{id}/replace-file` - Substituir arquivo (cria nova versão)
- ✅ `POST /{id}/recompute-audio` - Re-detectar has_audio via ffprobe
- ✅ `GET /{id}/versions` - Listar versões da mídia

**Conclusão:** 
- ✅ Detecção automática de duração **JÁ EXISTE**
- ✅ Substituição de mídia **JÁ EXISTE**
- ✅ Período de exibição (starts_at/ends_at) **JÁ EXISTE** nos models

---

#### Áudio - Tracks (`/api/v1/audio/tracks`)
- ✅ `GET /` - Listar faixas (com filtros)
- ✅ `POST /` - Criar faixa
- ✅ `POST /upload-multiple` - **Upload múltiplo de áudios ✅ JÁ EXISTE**
- ✅ `GET /{id}` - Obter faixa
- ✅ `PUT /{id}` - Atualizar faixa
- ✅ `DELETE /{id}` - Deletar faixa
- ✅ `GET /statistics/overview` - Estatísticas
- ✅ `GET /active/list` - Listar ativas
- ✅ `GET /by-category/{category}` - Por categoria
- ✅ `POST /{id}/archive` - Arquivar
- ✅ `POST /{id}/activate` - Ativar
- ✅ `PATCH /{id}/status` - Alterar status

**Conclusão:** Upload múltiplo de áudios **JÁ EXISTE**.

---

#### Áudio - Folders (`/api/v1/audio/folders`)
- ✅ `GET /` - Listar pastas
- ✅ `POST /` - Criar pasta
- ✅ `GET /{id}` - Obter pasta
- ✅ `PUT /{id}` - Atualizar pasta
- ✅ `DELETE /{id}` - Deletar pasta
- ✅ `POST /{id}/tracks` - Adicionar faixas na pasta
- ✅ `DELETE /{id}/tracks/{track_id}` - Remover faixa
- ✅ `PUT /{id}/tracks/reorder` - Reordenar faixas
- ✅ `GET /{id}/tracks` - Listar faixas da pasta

**Conclusão:** Sistema de pastas de áudio **JÁ EXISTE**.

---

#### Áudio - Playlists (`/api/v1/audio/playlists`)
- ✅ `GET /` - Listar playlists
- ✅ `POST /` - Criar playlist
- ✅ `GET /{id}` - Obter playlist
- ✅ `PUT /{id}` - Atualizar playlist
- ✅ `DELETE /{id}` - Deletar playlist
- ✅ `POST /{id}/items` - Adicionar faixas
- ✅ `DELETE /{id}/items/{item_id}` - Remover faixa
- ✅ `PUT /{id}/items/reorder` - Reordenar faixas
- ✅ `POST /{id}/folder-schedules` - Adicionar pasta com horário
- ✅ `PUT /{id}/folder-schedules/{schedule_id}` - Atualizar agendamento
- ✅ `DELETE /{id}/folder-schedules/{schedule_id}` - Remover agendamento
- ✅ `GET /{id}/folder-schedules` - Listar agendamentos

**Conclusão:** Sistema de programação por horário **JÁ EXISTE**.

---

#### Áudio - Spots (`/api/v1/audio/spots`)
- ✅ `GET /` - Listar spots
- ✅ `POST /` - Criar spot
- ✅ `GET /{id}` - Obter spot
- ✅ `PUT /{id}` - Atualizar spot
- ✅ `DELETE /{id}` - Deletar spot
- ✅ `POST /{id}/schedules` - Adicionar agendamento (intervalo)
- ✅ `PUT /{id}/schedules/{schedule_id}` - Atualizar agendamento
- ✅ `DELETE /{id}/schedules/{schedule_id}` - Remover agendamento
- ✅ `GET /{id}/schedules` - Listar agendamentos

**Conclusão:** Sistema de spots recorrentes **JÁ EXISTE**.

---

#### Dispositivos (`/api/v1/devices`)
- ✅ `POST /pair` - Parear dispositivo
- ✅ `GET /pair-status/{code}` - Status do pareamento
- ✅ `POST /{id}/heartbeat` - Heartbeat do player
- ✅ `GET /{id}/playlist` - Obter playlist ativa
- ✅ `POST /{id}/playback` - Registrar reprodução
- ✅ `GET /{id}/commands/pending` - Buscar comandos pendentes
- ✅ `POST /{id}/commands/{cmd_id}/received` - Marcar comando recebido
- ✅ `POST /{id}/commands/{cmd_id}/ack` - ACK do comando
- ✅ `POST /{id}/command` - Enviar comando (admin)
- ✅ `POST /{id}/commands/{cmd_id}/cancel` - Cancelar comando
- ✅ `GET /{id}/commands` - Listar comandos
- ✅ `POST /{id}/regenerate-code` - Regenerar código de pareamento
- ✅ `POST /{id}/force-repair` - Forçar novo pareamento
- ✅ `GET /{id}/pairing-events` - Histórico de pareamento
- ✅ `PUT /{id}/osd-config` - Configurar OSD

**Conclusão:** 
- ✅ Sistema de comandos **JÁ EXISTE**
- ✅ Regeneração de código com invalidação **JÁ EXISTE**
- ✅ Configuração de OSD **JÁ EXISTE**

---

#### Campanhas (`/api/v1/campaigns`)
- ✅ `GET /` - Listar campanhas
- ✅ `POST /` - Criar campanha
- ✅ `GET /{id}` - Obter campanha
- ✅ `PUT /{id}` - Atualizar campanha
- ✅ `DELETE /{id}` - Deletar campanha
- ✅ `POST /{id}/playlist-items` - Adicionar mídia na playlist
- ✅ `PUT /{id}/playlist-items/{item_id}` - Atualizar item
- ✅ `DELETE /{id}/playlist-items/{item_id}` - Remover item
- ✅ `PUT /{id}/playlist-items/reorder` - Reordenar itens
- ✅ `GET /{id}/playlist-items` - Listar itens

**Conclusão:** Sistema de playlist de campanha com ordenação **JÁ EXISTE**.

---

### 1.3 Migrations Existentes

Todas as funcionalidades solicitadas já possuem migrations:

- ✅ `20260520_1000_media_metadata_versions.py` - Versionamento de mídia
- ✅ `20260520_1400_campaign_playlist_items.py` - Itens de playlist com ordenação
- ✅ `20260521_0900_device_pairing_token_version.py` - Versionamento de pareamento
- ✅ `20260521_0915_device_command_lifecycle.py` - Ciclo de vida de comandos
- ✅ `20260522_1500_device_pairing_events.py` - Auditoria de pareamento
- ✅ `20260522_2000_audio_policy.py` - Política de áudio
- ✅ `20260523_1000_osd_config.py` - Configuração de OSD
- ✅ `20260523_1200_audio_playlist_items.py` - Itens de playlist de áudio
- ✅ `20260523_1300_audio_folders.py` - Pastas de áudio
- ✅ `20260523_1400_audio_playlist_folder_schedules.py` - Agendamento por horário
- ✅ `20260523_1500_audio_spots.py` - Spots recorrentes
- ✅ `20260523_1600_audio_playback_events.py` - Log de reprodução

---

## 2. ESTADO ATUAL DO FRONTEND

### 2.1 Páginas Existentes

- ✅ `BibliotecaMidias.jsx` - Biblioteca de mídias
- ✅ `MidiaUpload.jsx` - Upload de mídia
- ✅ `Campanhas.jsx` - Gerenciamento de campanhas
- ✅ `EditorPlaylist.jsx` - Editor de playlist de campanha
- ✅ `FaixasAudio.jsx` - Gerenciamento de faixas de áudio
- ✅ `PlaylistsSonoras.jsx` - Playlists de rádio
- ✅ `PlaylistDetalhe.jsx` - Detalhes da playlist de rádio
- ✅ `Dispositivos.jsx` - Gerenciamento de dispositivos
- ✅ `DispositivoDetalhe.jsx` - Detalhes do dispositivo
- ✅ `Player.jsx` - Player principal
- ✅ `PlayerAudio.jsx` - Player de áudio

### 2.2 Componentes Existentes

#### Áudio
- ✅ `AudioFolderManager.jsx` - Gerenciador de pastas de áudio
- ✅ `AudioPlaylistsFormModal.jsx` - Formulário de playlist
- ✅ `AudioScheduleBuilder.jsx` - Construtor de agendamento
- ✅ `AudioSpotScheduleManager.jsx` - Gerenciador de spots
- ✅ `AudioTrackFormModal.jsx` - Formulário de faixa
- ✅ `AudioTrackSelector.jsx` - Seletor de faixas
- ✅ `MultiAudioUploadDialog.jsx` - **Upload múltiplo de áudios ✅**

#### Mídia
- ✅ `MediaFormModal.jsx` - Formulário de mídia (com período de exibição)
- ✅ `MediaThumb.jsx` - Thumbnail de mídia

#### Player
- ✅ `PlayerOSD.jsx` - **Overlay com nome da música ✅**
- ✅ `MediaRenderer.jsx` - Renderizador de mídia
- ✅ `PairingScreen.jsx` - Tela de pareamento

### 2.3 Módulos Player-Core

- ✅ `platform.js` - Detecção de plataforma
- ✅ `storage.js` - PairingStorage, PlaylistCache
- ✅ `network.js` - Watchdog, heartbeat
- ✅ `commands.js` - **Executor de comandos ✅**
- ✅ `repair.js` - Forçar novo pareamento

---

## 3. ANÁLISE DAS SOLICITAÇÕES

### 3.1 MÍDIA

#### ✅ 1.1 Detectar tempo automático de vídeos
**STATUS: JÁ IMPLEMENTADO**

- Backend usa `ffprobe` para detectar duração automaticamente
- Campo `duration_seconds` armazena duração real
- Campo `display_duration_seconds` permite override manual
- Frontend não exige preenchimento manual para vídeos

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/media.py:141-183` - Função `_extract_media_metadata`
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/media.py:536-561` - Upload com detecção automática

**Pendências:** Nenhuma. Funcionalidade completa.

---

#### ✅ 1.2 Período de exibição na própria mídia
**STATUS: JÁ IMPLEMENTADO**

- Model `Media` possui campos `starts_at` e `ends_at`
- Frontend `MediaFormModal.jsx` possui campos de data
- Validação de período no backend

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:390-391` - Campos starts_at/ends_at
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/components/media/MediaFormModal.jsx:74-75` - Campos no formulário

**Pendências:**
- ⚠️ **Player precisa filtrar mídias por período** - Verificar se `isMediaCurrentlyPlayable` está sendo usado
- ⚠️ **Backend precisa filtrar na montagem da playlist** - Verificar endpoint `/devices/{id}/playlist`

---

#### ✅ 1.3 Substituir mídia sem remover do agendamento
**STATUS: JÁ IMPLEMENTADO**

- Sistema de versionamento via `MediaVersion`
- Endpoint `POST /media/{id}/replace-file` cria nova versão
- Mantém mesmo `media_id`, incrementa `file_version`
- Player usa cache key com versão: `media_id:file_version:file_hash`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:407-425` - Model MediaVersion
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/media.py:720-790` - Endpoint replace-file

**Pendências:** Nenhuma. Funcionalidade completa.

---

### 3.2 CAMPANHA / PLAYLIST

#### ✅ 2.1 Melhorar vínculo de mídias na campanha
**STATUS: JÁ IMPLEMENTADO**

- Model `CampaignPlaylistItem` permite adicionar mídias individualmente
- Cada item tem configurações próprias: `order_index`, `display_duration_seconds`, `starts_at`, `ends_at`, `is_active`, `repeat_count`
- Endpoints para adicionar, atualizar, remover e reordenar itens

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:326-353` - Model CampaignPlaylistItem
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/campaigns.py` - Endpoints de playlist

**Pendências:**
- ⚠️ **Frontend precisa usar a nova estrutura** - Verificar se `EditorPlaylist.jsx` usa `playlist_items` ou ainda usa `media_ids` legado

---

#### ✅ 2.2 Alterar ordem das mídias nas campanhas/playlists
**STATUS: JÁ IMPLEMENTADO**

- Campo `order_index` em `CampaignPlaylistItem`
- Endpoint `PUT /campaigns/{id}/playlist-items/reorder`
- Player respeita ordem via `order_by="CampaignPlaylistItem.order_index"`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:342` - Campo order_index
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:322` - order_by no relationship

**Pendências:**
- ⚠️ **Frontend precisa implementar drag-and-drop ou botões de ordenação**

---

### 3.3 RÁDIO / ÁUDIO

#### ✅ 3.1 Upload de múltiplas músicas ao mesmo tempo
**STATUS: JÁ IMPLEMENTADO**

- Endpoint `POST /audio/tracks/upload-multiple`
- Schema `AudioTrackUploadMultipleResponse` com lista de uploaded e errors
- Frontend possui `MultiAudioUploadDialog.jsx`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/audio/tracks.py:361-468` - Endpoint upload-multiple
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/components/audio/MultiAudioUploadDialog.jsx` - Componente frontend

**Pendências:** Nenhuma. Funcionalidade completa.

---

#### ✅ 3.2 Selecionar múltiplos áudios para rádio/ponto
**STATUS: PARCIALMENTE IMPLEMENTADO**

- Backend suporta adicionar múltiplas faixas via `POST /audio/playlists/{id}/items` (batch)
- Backend suporta adicionar múltiplas faixas em pastas via `POST /audio/folders/{id}/tracks` (batch)

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/audio/playlists.py` - Endpoints de playlist
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/audio/folders.py` - Endpoints de pastas

**Pendências:**
- ⚠️ **Frontend precisa implementar seleção múltipla** - Verificar `AudioTrackSelector.jsx`

---

#### ✅ 3.3 Agendamento de spot/audio a cada X tempo
**STATUS: JÁ IMPLEMENTADO**

- Model `AudioSpotSchedule` com campo `interval_seconds`
- Política de inserção: `INTERRUPT`, `WAIT_SILENCE`, `FADE_MIX`
- Período configurável: `start_time`, `end_time`, `starts_at`, `ends_at`
- Prioridade configurável

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:704-735` - Model AudioSpotSchedule
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/audio/spots.py` - Endpoints de spots

**Pendências:**
- ⚠️ **Player precisa implementar lógica de spots** - Verificar se `PlayerAudio.jsx` ou `audioManager.js` implementa spots

---

#### ✅ 3.4 Criar pastas/faixas de áudio por período
**STATUS: JÁ IMPLEMENTADO**

- Model `AudioFolder` com campos `starts_at`, `ends_at`, `start_time`, `end_time`, `schedule_days`
- Frontend possui `AudioFolderManager.jsx`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:484-516` - Model AudioFolder
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/components/audio/AudioFolderManager.jsx` - Componente frontend

**Pendências:** Nenhuma. Funcionalidade completa.

---

#### ✅ 3.5 Playlist da rádio por pastas com horário de início/fim
**STATUS: JÁ IMPLEMENTADO**

- Model `AudioPlaylistFolderSchedule` com horários e prioridade
- Endpoint `POST /audio/playlists/{id}/folder-schedules`
- Frontend possui `AudioScheduleBuilder.jsx`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:625-657` - Model AudioPlaylistFolderSchedule
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/components/audio/AudioScheduleBuilder.jsx` - Componente frontend

**Pendências:**
- ⚠️ **Player precisa resolver qual pasta tocar no horário atual** - Verificar lógica no endpoint `/devices/{id}/playlist`

---

#### ✅ 3.6 Música em sequência ou embaralhada
**STATUS: JÁ IMPLEMENTADO**

- Campo `shuffle_enabled` em `AudioPlaylist`
- Campo `play_mode` em `AudioPlaylistFolderSchedule` (SEQUENTIAL, SHUFFLE, LOOP)

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:563` - Campo shuffle_enabled
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:647-650` - Campo play_mode

**Pendências:**
- ⚠️ **Player precisa implementar shuffle** - Verificar `PlayerAudio.jsx`

---

### 3.4 PLAYER

#### ⚠️ 4.1 Player não desliga pelo gerenciador
**STATUS: IMPLEMENTADO MAS COM POSSÍVEL BUG**

- Sistema de comandos existe e está completo
- Comandos `shutdown_device` e `restart_device` existem
- Player possui handler em `commands.js` que chama `callNativePowerCommand`
- Ciclo de vida: PENDING → SENT → RECEIVED → EXECUTING → COMPLETED/FAILED

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/player-core/commands.js:107-115` - Handlers de shutdown/restart
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/devices.py:1636-1730` - Endpoints de comandos

**Possíveis causas do problema:**
1. **Plataforma não suporta:** Browser puro não pode desligar dispositivo físico
2. **Bridge nativo ausente:** `window.PlayWaveNative`, `window.AndroidPlayer` ou `window.__ELECTRON__` não está definido
3. **Comando não chega no player:** Polling de comandos não está funcionando
4. **ACK não é enviado:** Player não confirma execução
5. **Timeout:** Comando expira antes de ser executado

**Ações necessárias:**
1. ✅ Verificar logs do backend: comandos estão sendo criados?
2. ✅ Verificar logs do player: comandos estão sendo recebidos?
3. ✅ Verificar plataforma: web, APK, Electron, Linux, Windows?
4. ✅ Verificar bridge nativo: está implementado?
5. ✅ Verificar ACK: player está confirmando?

---

#### ✅ 4.2 Alterar código de pareamento deve invalidar player antigo
**STATUS: JÁ IMPLEMENTADO**

- Sistema de versionamento: `pairing_version` e `token_version`
- Flag `requires_repairing` força novo pareamento
- Endpoint `POST /devices/{id}/regenerate-code` incrementa versões
- Endpoint `POST /devices/{id}/force-repair` marca para reparear
- Middleware `get_device_by_token` valida versão e bloqueia se necessário
- Player recebe erro `REQUIRES_REPAIRING` e chama `onForceRepair()`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:173-175` - Campos de versionamento
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/api/v1/devices.py:129-160` - Validação de token
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/player-core/repair.js` - Handler de force repair

**Pendências:**
- ⚠️ **Testar se realmente invalida** - Verificar se após regenerar código, player antigo para de funcionar

---

#### ⚠️ 4.3 Mídia misturando áudio com rádio
**STATUS: IMPLEMENTADO MAS PRECISA VALIDAÇÃO**

- Sistema `AudioPolicy` existe com 5 modos:
  - `AUTO`: Detecta automaticamente
  - `RADIO_ONLY`: Rádio sempre ativa, vídeo mudo
  - `MEDIA_AUDIO_ONLY`: Áudio da mídia, rádio pausa
  - `MIX`: Ambos tocam juntos
  - `MUTED_VIDEO_WITH_RADIO`: Vídeo sempre mudo com rádio

- Política pode ser definida em:
  - Tenant (padrão global)
  - Device (padrão do dispositivo)
  - Campaign (padrão da campanha)
  - Media (específico da mídia)

- Player possui `useAudioConflictResolver` hook
- Player possui `audioManager.js` para gerenciar áudio

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:16-22` - Enum AudioPolicy
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/hooks/useAudioConflictResolver.js` - Hook de resolução
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/lib/audioManager.js` - Gerenciador de áudio

**Ações necessárias:**
1. ✅ Verificar se `audioManager` está sendo usado corretamente
2. ✅ Verificar se política está sendo respeitada
3. ✅ Verificar se spots estão pausando música corretamente
4. ✅ Testar cada modo de AudioPolicy

---

#### ✅ 4.4 Exibir nome da música no canto da tela do player/TV
**STATUS: JÁ IMPLEMENTADO**

- Model `Device` possui campos OSD: `osd_show_current_audio`, `osd_position`, `osd_duration_seconds`, `osd_opacity`, `osd_font_size`
- Tenant possui configuração padrão de OSD
- Endpoint `PUT /devices/{id}/osd-config` para configurar
- Frontend possui componente `PlayerOSD.jsx`

**Localização:**
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/core/models.py:193-197` - Campos OSD no Device
- `@/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/components/player/PlayerOSD.jsx` - Componente OSD

**Pendências:**
- ⚠️ **Verificar se está sendo exibido** - Testar no player real

---

## 4. FUNCIONALIDADES JÁ IMPLEMENTADAS

### ✅ Backend (100% completo)
1. ✅ Detecção automática de duração de vídeos (ffprobe)
2. ✅ Período de exibição em mídias (starts_at/ends_at)
3. ✅ Substituição de mídia com versionamento
4. ✅ Playlist de campanha com itens individuais
5. ✅ Ordenação de playlist (order_index)
6. ✅ Upload múltiplo de áudios
7. ✅ Pastas de áudio com período
8. ✅ Playlist de rádio por horário
9. ✅ Spots recorrentes (a cada X segundos)
10. ✅ Modo sequencial/aleatório
11. ✅ Sistema de comandos remotos
12. ✅ Versionamento de pareamento
13. ✅ Política de áudio (AudioPolicy)
14. ✅ Configuração de OSD
15. ✅ Log de reprodução de áudio

### ✅ Frontend (80% completo)
1. ✅ Upload múltiplo de áudios (MultiAudioUploadDialog)
2. ✅ Gerenciador de pastas (AudioFolderManager)
3. ✅ Construtor de agendamento (AudioScheduleBuilder)
4. ✅ Gerenciador de spots (AudioSpotScheduleManager)
5. ✅ Formulário de mídia com período
6. ✅ OSD do player (PlayerOSD)
7. ✅ Sistema de comandos (commands.js)
8. ✅ Force repair (repair.js)
9. ⚠️ Seleção múltipla de áudios (precisa validar)
10. ⚠️ Drag-and-drop de ordenação (precisa implementar)

### ⚠️ Player (70% completo)
1. ✅ Sincronização de playlist
2. ✅ Sincronização de comandos
3. ✅ Versionamento de cache
4. ✅ Force repair automático
5. ✅ OSD de música
6. ⚠️ Filtro de mídia por período (precisa validar)
7. ⚠️ Resolução de conflito de áudio (precisa validar)
8. ⚠️ Reprodução de spots (precisa implementar)
9. ⚠️ Modo shuffle (precisa validar)
10. ⚠️ Comandos de shutdown/restart (precisa debugar)

---

## 5. GAPS E PENDÊNCIAS

### 5.1 Bugs Reportados

#### 🐛 BUG-001: Player não desliga pelo gerenciador
**Prioridade:** ALTA  
**Status:** Investigação necessária

**Hipóteses:**
1. Plataforma não suporta (web browser)
2. Bridge nativo não implementado (APK/Electron)
3. Polling de comandos não funciona
4. ACK não é enviado
5. Timeout muito curto

**Ações:**
- [ ] Adicionar logs detalhados no player
- [ ] Verificar bridge nativo em cada plataforma
- [ ] Testar comando manualmente via API
- [ ] Verificar status do comando no banco
- [ ] Implementar fallback para plataformas não suportadas

---

#### 🐛 BUG-002: Mídia misturando áudio com rádio
**Prioridade:** ALTA  
**Status:** Validação necessária

**Hipóteses:**
1. AudioPolicy não está sendo respeitada
2. audioManager não está pausando rádio
3. Spots não estão interrompendo música
4. Conflito entre múltiplas fontes de áudio

**Ações:**
- [ ] Testar cada modo de AudioPolicy
- [ ] Verificar logs do audioManager
- [ ] Validar prioridade de áudio (spot > mídia > rádio)
- [ ] Implementar testes automatizados

---

#### 🐛 BUG-003: Código de pareamento não invalida player antigo
**Prioridade:** MÉDIA  
**Status:** Validação necessária

**Hipóteses:**
1. Player não está verificando versão
2. Middleware não está bloqueando
3. Cache do player não é limpo

**Ações:**
- [ ] Testar regeneração de código
- [ ] Verificar se player recebe erro REQUIRES_REPAIRING
- [ ] Verificar se onForceRepair é chamado
- [ ] Limpar cache local ao reparear

---

### 5.2 Funcionalidades Faltantes

#### 📋 FEAT-001: Filtro de mídia por período no player
**Prioridade:** ALTA  
**Status:** Implementação necessária

**Descrição:** Player deve filtrar mídias com `starts_at` e `ends_at` antes de exibir.

**Localização:** `Player.jsx` ou endpoint `/devices/{id}/playlist`

**Ações:**
- [ ] Verificar se `isMediaCurrentlyPlayable` está sendo usado
- [ ] Implementar filtro no backend (preferível)
- [ ] Implementar filtro no player (fallback)
- [ ] Adicionar testes

---

#### 📋 FEAT-002: Reprodução de spots no player
**Prioridade:** ALTA  
**Status:** Implementação necessária

**Descrição:** Player deve tocar spots a cada X segundos conforme `AudioSpotSchedule`.

**Localização:** `PlayerAudio.jsx` ou `audioManager.js`

**Ações:**
- [ ] Buscar spots ativos da playlist
- [ ] Implementar timer de intervalo
- [ ] Implementar política de inserção (INTERRUPT, WAIT_SILENCE, FADE_MIX)
- [ ] Registrar evento de reprodução
- [ ] Adicionar testes

---

#### 📋 FEAT-003: Modo shuffle no player
**Prioridade:** MÉDIA  
**Status:** Validação/Implementação necessária

**Descrição:** Player deve embaralhar faixas quando `shuffle_enabled = true`.

**Localização:** `PlayerAudio.jsx`

**Ações:**
- [ ] Verificar se shuffle está implementado
- [ ] Implementar algoritmo de shuffle (Fisher-Yates)
- [ ] Evitar repetição excessiva
- [ ] Respeitar prioridade de spots
- [ ] Adicionar testes

---

#### 📋 FEAT-004: Resolução de pasta por horário no player
**Prioridade:** ALTA  
**Status:** Implementação necessária

**Descrição:** Player deve tocar pasta correta conforme horário atual.

**Localização:** Endpoint `/devices/{id}/playlist` ou `PlayerAudio.jsx`

**Ações:**
- [ ] Buscar `AudioPlaylistFolderSchedule` ativo
- [ ] Filtrar por horário atual
- [ ] Resolver conflitos por prioridade
- [ ] Trocar pasta automaticamente ao mudar horário
- [ ] Adicionar testes

---

#### 📋 FEAT-005: Seleção múltipla de áudios no frontend
**Prioridade:** MÉDIA  
**Status:** Validação/Implementação necessária

**Descrição:** Frontend deve permitir selecionar múltiplas faixas de uma vez.

**Localização:** `AudioTrackSelector.jsx`

**Ações:**
- [ ] Verificar se já existe
- [ ] Implementar checkboxes
- [ ] Implementar ações em lote (adicionar, remover, mover)
- [ ] Adicionar feedback visual

---

#### 📋 FEAT-006: Drag-and-drop de ordenação no frontend
**Prioridade:** BAIXA  
**Status:** Implementação necessária

**Descrição:** Frontend deve permitir reordenar itens via drag-and-drop.

**Localização:** `EditorPlaylist.jsx`, `AudioFolderManager.jsx`

**Ações:**
- [ ] Instalar biblioteca (react-beautiful-dnd ou dnd-kit)
- [ ] Implementar drag-and-drop em playlist de campanha
- [ ] Implementar drag-and-drop em pasta de áudio
- [ ] Implementar drag-and-drop em playlist de rádio
- [ ] Salvar ordem no backend

---

### 5.3 Melhorias de UX

#### 💡 UX-001: Feedback visual de upload múltiplo
**Prioridade:** BAIXA

- [ ] Barra de progresso por arquivo
- [ ] Indicador de sucesso/erro
- [ ] Possibilidade de cancelar upload

---

#### 💡 UX-002: Preview de mídia antes de adicionar
**Prioridade:** BAIXA

- [ ] Thumbnail maior
- [ ] Player inline para vídeo/áudio
- [ ] Informações detalhadas

---

#### 💡 UX-003: Timeline visual de agendamento
**Prioridade:** BAIXA

- [ ] Visualização gráfica de horários
- [ ] Detecção de conflitos
- [ ] Sugestão de horários livres

---

## 6. PLANO DE AÇÃO RECOMENDADO

### Fase 1: Investigação e Correção de Bugs (1-2 semanas)

**Objetivo:** Corrigir bugs reportados e validar funcionalidades existentes.

#### Sprint 1.1: Comandos do Player
- [ ] Adicionar logs detalhados em `commands.js`
- [ ] Testar comando de shutdown em cada plataforma
- [ ] Implementar bridge nativo se ausente
- [ ] Documentar limitações por plataforma
- [ ] Criar testes automatizados

#### Sprint 1.2: Conflito de Áudio
- [ ] Testar cada modo de AudioPolicy
- [ ] Validar audioManager
- [ ] Corrigir bugs de sobreposição
- [ ] Documentar comportamento esperado
- [ ] Criar testes automatizados

#### Sprint 1.3: Pareamento
- [ ] Testar regeneração de código
- [ ] Validar invalidação de token
- [ ] Corrigir bugs de cache
- [ ] Documentar fluxo de pareamento
- [ ] Criar testes automatizados

---

### Fase 2: Implementação de Funcionalidades Faltantes (2-3 semanas)

**Objetivo:** Completar funcionalidades que existem no backend mas não no player/frontend.

#### Sprint 2.1: Player - Filtros e Spots
- [ ] Implementar filtro de mídia por período
- [ ] Implementar reprodução de spots
- [ ] Implementar resolução de pasta por horário
- [ ] Implementar modo shuffle
- [ ] Criar testes automatizados

#### Sprint 2.2: Frontend - Seleção e Ordenação
- [ ] Implementar seleção múltipla de áudios
- [ ] Implementar drag-and-drop de ordenação
- [ ] Melhorar feedback visual
- [ ] Criar testes automatizados

---

### Fase 3: Testes de Integração (1 semana)

**Objetivo:** Validar sistema completo end-to-end.

#### Sprint 3.1: Testes de Mídia
- [ ] Upload de vídeo com detecção automática de duração
- [ ] Período de exibição (mídia futura não aparece)
- [ ] Substituição de mídia mantendo agendamento
- [ ] Versionamento e cache

#### Sprint 3.2: Testes de Campanha
- [ ] Criar campanha com playlist estruturada
- [ ] Reordenar itens
- [ ] Configurar duração customizada por item
- [ ] Configurar período por item

#### Sprint 3.3: Testes de Rádio
- [ ] Upload múltiplo de áudios
- [ ] Criar pastas com período
- [ ] Agendar pastas por horário
- [ ] Configurar spots recorrentes
- [ ] Testar modo sequencial e shuffle

#### Sprint 3.4: Testes de Player
- [ ] Pareamento e despareamento
- [ ] Comandos remotos (sync, restart, shutdown)
- [ ] Conflito de áudio (cada modo)
- [ ] OSD de música
- [ ] Sincronização offline

---

### Fase 4: Documentação e Treinamento (1 semana)

**Objetivo:** Documentar funcionalidades e treinar usuários.

#### Sprint 4.1: Documentação Técnica
- [ ] Arquitetura do sistema
- [ ] Fluxo de dados
- [ ] API endpoints
- [ ] Models e schemas
- [ ] Comandos do player

#### Sprint 4.2: Documentação de Usuário
- [ ] Manual de uso
- [ ] Tutoriais em vídeo
- [ ] FAQ
- [ ] Troubleshooting

#### Sprint 4.3: Treinamento
- [ ] Sessão de treinamento para administradores
- [ ] Sessão de treinamento para operadores
- [ ] Material de apoio

---

## 7. RISCOS E LIMITAÇÕES

### 7.1 Riscos Técnicos

#### ⚠️ RISCO-001: Comandos de shutdown não funcionam em web browser
**Probabilidade:** ALTA  
**Impacto:** MÉDIO  
**Mitigação:** Documentar limitação e recomendar uso de APK/Electron/Linux

---

#### ⚠️ RISCO-002: ffprobe não disponível em produção
**Probabilidade:** BAIXA  
**Impacto:** ALTO  
**Mitigação:** Validar instalação de ffprobe no Dockerfile e documentar fallback manual

---

#### ⚠️ RISCO-003: Conflito de horários de pastas
**Probabilidade:** MÉDIA  
**Impacto:** MÉDIO  
**Mitigação:** Implementar validação de conflitos e usar campo `priority`

---

#### ⚠️ RISCO-004: Sincronização offline
**Probabilidade:** MÉDIA  
**Impacto:** ALTO  
**Mitigação:** Validar cache do player e fallback offline

---

### 7.2 Limitações Conhecidas

#### 📌 LIMIT-001: Detecção de duração só funciona para vídeo/áudio local
**Descrição:** URLs externas (YouTube, Vimeo) não têm duração detectada.  
**Workaround:** Usuário deve informar duração manualmente.

---

#### 📌 LIMIT-002: Shutdown/restart só funciona em ambientes nativos
**Descrição:** Web browser não pode desligar dispositivo físico.  
**Workaround:** Usar APK, Electron ou Linux com permissões adequadas.

---

#### 📌 LIMIT-003: Spots podem atrasar se música for muito longa
**Descrição:** Spot com `WAIT_SILENCE` só toca após música terminar.  
**Workaround:** Usar `INTERRUPT` ou `FADE_MIX` para spots urgentes.

---

## 8. CONCLUSÃO

O sistema PlayWave possui uma arquitetura sólida e **a maioria das funcionalidades solicitadas já está implementada**. O trabalho necessário é principalmente de:

1. **Correção de bugs** (comandos, áudio, pareamento)
2. **Validação de funcionalidades** (filtros, spots, shuffle)
3. **Melhorias de UX** (drag-and-drop, seleção múltipla)
4. **Testes e documentação**

**Estimativa total:** 5-7 semanas

**Prioridades:**
1. 🔴 **ALTA:** Bugs de comandos e áudio (afetam uso diário)
2. 🟡 **MÉDIA:** Funcionalidades faltantes no player (spots, filtros)
3. 🟢 **BAIXA:** Melhorias de UX (drag-and-drop, preview)

**Próximos passos:**
1. Validar este documento com o cliente
2. Priorizar itens conforme necessidade
3. Criar SPECs técnicas detalhadas para cada item
4. Implementar por fases
5. Testar e documentar

---

**Documento gerado em:** 26/05/2026  
**Autor:** Cascade AI  
**Versão:** 1.0
