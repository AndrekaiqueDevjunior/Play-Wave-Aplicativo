# SPEC 017 — Design

Status: implementada

## Fluxo esperado (listagem, arquivar/restaurar, excluir)

Idêntico ao desenhado na SPEC 016 (`docs/specs/016-faixas-audio-arquivar-excluir/design.md`), substituindo `AudioTrack` por `AudioPlaylist`. Não repetido aqui na íntegra — a diferença real desta SPEC está na checagem de uso e no resolver do player, detalhadas abaixo.

## Decisão técnica: checagem de uso via FK direta, não tabela de junção

A SPEC 016 verificava uso de uma `AudioTrack` em 3 tabelas de junção (`AudioPlaylistItem`, `AudioFolderTrack`, `AudioSpot`), todas com `ondelete="RESTRICT"`. Para `AudioPlaylist`, a auditoria encontrou uma estrutura diferente: `Device.audio_playlist_id` e `Campaign.audio_playlist_id` são colunas **diretas** na própria tabela de device/campanha, sem `ondelete` definido (o que o Postgres trata como `RESTRICT` implícito).

`CRUDAudioPlaylist.get_in_use_references()` reflete essa diferença: conta `Device` e `Campaign` filtrando por `audio_playlist_id == playlist_id`, em vez de contar linhas em uma tabela de junção. O resultado (`{"devices": N, "campaigns": M, "in_use": bool}`) segue o mesmo formato usado pela SPEC 016, para manter o padrão de resposta de erro consistente entre os dois recursos.

## Decisão técnica: dois pontos de resolução do player, dois tratamentos diferentes

A auditoria inicial (feita antes de ler o código com cuidado) sugeria que o player não filtrava playlists arquivadas. Uma leitura mais profunda de `backend/api/v1/devices.py` revelou que isso estava errado para o caminho real:

- `_build_audio_playlist()` (linha ~661) já filtra por `status == "active"` antes de montar o payload do device.
- `_build_player_playlist_response()` (linha ~681), que resolve a playlist tanto via campanha (`campaign.audio_playlist_id`) quanto via device (`device.audio_playlist_id`), também já checa `status == "active"` em ambos os ramos.
- `get_device_playlist()` (o endpoint real, `GET /devices/{device_id}/playlist`, usado pelo `Player.jsx` em produção) delega para `_build_player_playlist_response()` — portanto **já estava protegido antes desta SPEC**.

O que realmente não filtrava era um **segundo endpoint**, `GET /audio/devices/{device_id}/playlist` (arquivo `backend/api/v1/audio/devices.py`), registrado no FastAPI (`main.py` inclui esse router) mas **não chamado por nenhum lugar do frontend atual** (`buscarPlaylistAudioDispositivo` existe em `api/audio.js` mas não tem nenhum import/uso). Mesmo sendo código não utilizado pelo player real hoje, é uma rota viva e alcançável — corrigida por precaução e consistência, com o mesmo filtro `status == "active"` já usado no caminho principal.

Essa distinção foi importante para não superestimar o escopo do bug nem alterar código que já estava correto (risco de regressão sem benefício).

## Pontos de auditoria realizados

- [x] Confirmar `GET /audio/playlists` sem filtro de arquivadas por padrão — causa raiz do leak, confirmado.
- [x] Confirmar os 4 seletores existentes (`DeviceEditDrawer.jsx`, `DeviceFormModal.jsx`, `Campanhas.jsx`/`CampaignFormModal.jsx`, `Spots.jsx`) já filtram por `status=active` — preservados sem alteração.
- [x] Confirmar `_build_audio_playlist`/`_build_player_playlist_response` em `backend/api/v1/devices.py` já filtram por `status == "active"` — sem mudança necessária no resolver principal.
- [x] Confirmar `GET /audio/devices/{device_id}/playlist` (`backend/api/v1/audio/devices.py`) não filtrava — corrigido.
- [x] Confirmar que esse segundo endpoint está registrado (`main.py`) mas não é chamado pelo frontend atual (`buscarPlaylistAudioDispositivo` sem nenhum import) — corrigido por precaução, sem risco de regressão visível ao usuário.
- [x] Confirmar `Device.audio_playlist_id`/`Campaign.audio_playlist_id` como FK direta sem `ondelete` — guiou o desenho de `get_in_use_references()`.
- [x] Confirmar `PlaylistsSonoras.jsx` sem distinção Arquivar/Excluir e sem filtro de status — mesmo padrão de bug de UI da SPEC 016.

## Arquivos impactados

- `backend/core/models.py` — campo `archived_at` em `AudioPlaylist`.
- `backend/core/schemas_completos.py` — `archived_at` em `AudioPlaylistResponse`.
- `backend/api/v1/audio/playlists.py` — `include_archived` em `GET /`, checagem de uso em `DELETE /{id}`.
- `backend/api/v1/audio/devices.py` — filtro `status == "active"` no endpoint secundário de resolução.
- `backend/crud/entidades/crud_audio_playlist.py` — override de `update()`, `update_status()` delega para `update()`, novo `get_in_use_references()`.
- `backend/alembic/versions/20260618_1300_audio_playlist_archived_at.py` — migration aditiva.
- `frontend/src/pages/PlaylistsSonoras.jsx` — filtro de status, separação Arquivar/Restaurar/Excluir, `include_archived=true` na query própria.
- `backend/tests/test_audio_playlist_archive_delete.py` — testes novos.

Não foram necessárias mudanças em:

- `backend/api/v1/devices.py` (`_build_audio_playlist`, `_build_player_playlist_response`, `get_device_playlist`) — caminho real do player já correto.
- `frontend/src/components/devices/DeviceEditDrawer.jsx`, `DeviceFormModal.jsx`, `frontend/src/pages/Campanhas.jsx`, `CampaignFormModal.jsx`, `Spots.jsx` — já filtravam `status=active`.

## Riscos

- Se um `Device`/`Campaign` já está vinculado a uma playlist e ela é arquivada depois, o vínculo (`audio_playlist_id`) permanece no banco, apenas o conteúdo deixa de ser servido (RF017-03). O admin não recebe nenhum aviso de que o device está "órfão" de áudio — fora de escopo desta SPEC (ver `README.md`), pendência registrada para uma melhoria futura de UX.
- Migration tem backfill (`archived_at = now()`) com a mesma limitação de precisão da SPEC 016 (data exata do arquivamento original é desconhecida).
- O fix no endpoint secundário (`audio/devices.py`) não tem cobertura de teste automatizado nesta SPEC (não há suite de testes pré-existente para esse arquivo) — validado apenas por revisão manual de código.
- Migration não aplicada em produção (VPS) nesta sessão.
