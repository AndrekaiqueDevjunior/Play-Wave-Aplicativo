# SPEC 018 — Mídias: Exclusão/Arquivamento em Massa

Status: implementada — testes de frontend passando; testes de backend validados por sintaxe (pytest não executável neste ambiente); deploy/migration pendente
Data: 2026-06-18
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-009)

## Objetivo

Permitir seleção múltipla na tela de Mídias para arquivar/excluir em lote, respeitando dependências (campanhas) e reportando sucesso/falha por item — e, como pré-requisito, criar a capacidade de arquivamento para Mídia, que (diferente de `AudioTrack`/`AudioPlaylist`) ainda não existia antes desta SPEC.

## Regra de sequenciamento

Esta SPEC entrou em implementação após a `SPEC 017 — Playlist Sonora Arquivar/Restaurar/Excluir` ser concluída (170/173 testes de frontend sem regressão).

## Diagnóstico resumido

Diferente das SPECs 016/017 (onde o arquivamento já existia e o bug era leak de filtro), Mídia tinha uma lacuna mais fundamental:

- **Sem capacidade de arquivar**: o model `Media` só tinha `MediaStatus` com `AVAILABLE`/`PROCESSING`/`ERROR` — nenhum estado `ARCHIVED`, nenhum `archived_at`. "Arquivar" simplesmente não existia como conceito para mídia.
- **Exclusão única já fazia hard delete real**, com uma checagem de uso (`_campaigns_using_media`) — mas essa checagem só olhava os campos legados `Campaign.media_ids`/`media_order` (JSON), **não** a tabela relacional `CampaignPlaylistItem` (que tem FK `RESTRICT` e é o caminho real que o player usa para resolver o conteúdo da campanha, conforme `backend/api/v1/devices.py`). Uma mídia referenciada só em `CampaignPlaylistItem` podia estourar erro de banco não tratado ao tentar excluir, mesmo com `force=True` (que só desvincula os campos legados).
- **Nenhuma seleção múltipla na UI**: `BibliotecaMidias.jsx` não tinha nenhum padrão de checkbox/seleção em massa — diferente de `FaixasAudio.jsx`/`PlaylistsSonoras.jsx`, que já ganharam esse padrão nas SPECs 016/017.
- **Nenhum endpoint bulk no backend**: todas as ações (arquivar, excluir) só existiam item por item.

## Decisão de escopo (confirmada com o usuário)

- Criar `archived_at` + `MediaStatus.ARCHIVED` nesta SPEC, seguindo o mesmo padrão das SPECs 016/017 (em vez de deixar para a SPEC 020).
- Corrigir a checagem de uso para também contar `CampaignPlaylistItem`, já que o bulk delete reaproveita essa lógica — uma checagem incompleta no bulk seria pior que no single delete, pois processaria múltiplos itens com a mesma lacuna.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho técnico do bulk, checagem de uso dupla (relacional + legado) e por que o bulk não tem `force`.
- `api-contract.md` — contrato de `POST /media/bulk-archive`, `POST /media/bulk-delete` e mudanças em `GET /media`/`DELETE /media/{id}`.
- `player.md` — confirmação de que a resolução de campanha do player não precisa de mudança (já lê de `CampaignPlaylistItem` com seus próprios filtros).
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidências.

## Fora de escopo

- Padronizar `deleted_at` — fica para a `SPEC 020 — Padrão Arquivamento vs Exclusão`.
- Desvincular automaticamente `CampaignPlaylistItem` ao excluir (em massa ou individualmente) — decisão deliberada de manter como bloqueio explícito, não auto-remoção (ver `design.md`).
- Endpoint bulk de restauração (`bulk-restore`) — não pedido no documento mestre; restaurar continua item por item nesta SPEC.
- Migration aplicada em produção (VPS) — pendente de deploy, mesma situação das SPECs anteriores.
