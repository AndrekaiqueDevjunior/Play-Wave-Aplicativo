# SPEC 017 — Playlist Sonora: Arquivar/Restaurar/Excluir

Status: implementada — testes de frontend passando; testes de backend validados por sintaxe (pytest não executável neste ambiente); deploy/migration pendente
Data: 2026-06-18
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-004)

## Objetivo

Aplicar à Playlist Sonora (`AudioPlaylist`) o mesmo padrão de Arquivar/Restaurar/Excluir definitivamente já corrigido para Faixas de Áudio na `SPEC 016`, garantindo que playlists arquivadas não apareçam em seletores (device, campanha) nem sejam servidas ao player.

## Regra de sequenciamento

Esta SPEC entrou em implementação após a `SPEC 016 — Faixas de Áudio: Arquivar/Restaurar/Excluir` ser concluída (170/173 testes de frontend sem regressão).

## Diagnóstico resumido

O mesmo padrão de leak da SPEC 016 se repetia para playlists, com uma complicação adicional:

- **Leak idêntico**: `GET /audio/playlists` não filtrava arquivadas por padrão — afetando os seletores de playlist em `DeviceEditDrawer.jsx`/`DeviceFormModal.jsx` (vincular playlist a um device), `Campanhas.jsx`/`CampaignFormModal.jsx` (vincular a uma campanha) e `Spots.jsx`. (Esses 4 call sites já filtravam por `status: "active"` explicitamente e não foram afetados pelo bug — o leak real só acontecia na própria tela de gerenciamento, `PlaylistsSonoras.jsx`, que listava tudo sem filtro nem opção de ver arquivadas separadamente.)
- **UI sem distinção**: igual à SPEC 016 antes da correção, o botão de "excluir" em `PlaylistsSonoras.jsx` só arquivava (`PUT` com `status: archived`), sem caminho de UI para restaurar ou excluir definitivamente.
- **Excluir definitivamente sem checagem de uso**: `DELETE /audio/playlists/{id}` fazia hard delete real, mas sem verificar se algum `Device.audio_playlist_id` ou `Campaign.audio_playlist_id` ainda apontava para a playlist — diferente das faixas (referenciadas via tabelas de junção com `RESTRICT`), aqui são FKs diretas sem `ondelete` definido, que também falhariam com erro genérico de banco.
- **Bug adicional, mais sério que o das faixas**: a resolução de playlist do player (`_build_audio_playlist`/`_build_player_playlist_response` em `backend/api/v1/devices.py`) **já filtrava corretamente por `status == "active"`** — então o player principal nunca tocava uma playlist arquivada. Porém, um endpoint secundário e não utilizado pelo frontend atual (`GET /audio/devices/{device_id}/playlist`, em `backend/api/v1/audio/devices.py`) **não tinha esse filtro** — uma playlist arquivada, se referenciada, era servida integralmente por esse caminho.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho técnico do filtro, archived_at e checagem de uso (FK direta vs. tabela de junção).
- `api-contract.md` — contrato de `GET /audio/playlists` e `DELETE /audio/playlists/{id}`.
- `player.md` — confirmação do que já estava correto no resolver principal e a correção do endpoint secundário.
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidências.

## Fora de escopo

- Padronizar `deleted_at` — fica para a `SPEC 020 — Padrão Arquivamento vs Exclusão`.
- Aviso na UI quando um device/campanha está vinculado a uma playlist já arquivada (apenas o bloqueio no resolver do player foi implementado; um aviso visual no `DeviceEditDrawer.jsx` é melhoria de UX, não correção de bug).
- Aplicar o mesmo padrão a Mídias — isso é o objetivo da `SPEC 018`.
- Migration aplicada em produção (VPS) — pendente de deploy, mesma situação das SPECs anteriores.
