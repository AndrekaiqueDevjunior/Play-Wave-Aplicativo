# SPEC 018 — Player

Status: implementada — nenhuma mudança necessária no player

## Comportamento confirmado

A resolução de conteúdo de campanha do player (`backend/api/v1/devices.py`) lê de `CampaignPlaylistItem` com seus próprios filtros (`is_active`, janelas de `starts_at`/`ends_at`, etc.) — independente de qualquer alteração feita nesta SPEC.

Esta SPEC não introduz nenhum estado de mídia que o player precise passar a ignorar: mídias arquivadas continuam podendo estar referenciadas em `CampaignPlaylistItem` (o arquivamento de uma mídia, sozinho, não remove vínculos existentes — ver `design.md`). Se isso é desejável o suficiente para o cliente, fica registrado como pendência de UX (mesma decisão tomada na SPEC 017 para `Device`/`AudioPlaylist`): o admin não recebe aviso automático de que uma campanha referencia uma mídia já arquivada.

## Por que não foi necessária mudança aqui

- O player nunca consultou `Media.status` diretamente para decidir o que exibir — ele resolve via `CampaignPlaylistItem`, que tem seu próprio ciclo de vida (`is_active`).
- Esta SPEC trata de gerenciamento (arquivar/excluir mídias na biblioteca), não da composição de conteúdo de uma campanha já publicada.

## Checklist de auditoria

- [x] Conferir `backend/api/v1/devices.py` — resolução de `CampaignPlaylistItem` não depende de `Media.status`.
- [x] Confirmar que arquivar uma mídia não desvincula `CampaignPlaylistItem` automaticamente — comportamento deliberado (ver `design.md`), não uma omissão.
- [x] Confirmar que a checagem de uso nova (`get_in_use_references`) é usada apenas pelos endpoints de exclusão definitiva (`DELETE`, `bulk-delete`), nunca pelo caminho de resolução do player.
