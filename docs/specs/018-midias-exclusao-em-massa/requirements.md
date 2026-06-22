# SPEC 018 — Requirements

Status: implementada
Data: 2026-06-18

## Contexto

Cliente reportou que a exclusão de mídias está limitada a uma por vez e pediu seleção múltipla. A auditoria confirmou que não havia nenhum mecanismo de seleção em massa na UI, nenhum endpoint bulk no backend, e — diferente de faixas/playlists de áudio — Mídia nem tinha o conceito de "arquivar" implementado.

## Objetivo

Permitir selecionar várias mídias e aplicar arquivamento ou exclusão definitiva em lote, com resultado por item (sucesso/falha/motivo), respeitando dependências (mídia em uso por campanha).

## Requisitos funcionais

### RF018-01 — Capacidade de arquivar mídia (pré-requisito)

Mídia precisa de um estado "arquivada", distinto de excluída e dos estados de processamento existentes.

Critérios:

- Novo valor `archived` no enum `MediaStatus`.
- Campo `archived_at` (nullable), sincronizado automaticamente com o status em qualquer caminho de update.
- `GET /media` esconde mídias arquivadas por padrão (`include_archived` para ver explicitamente), mesmo padrão das SPECs 016/017.

### RF018-02 — Seleção múltipla na UI

A tela de Mídias deve permitir selecionar vários itens e aplicar uma ação em lote.

Critérios:

- Modo de seleção com checkbox por item (grid e lista).
- "Selecionar todas" (dentro do filtro atual) e "Limpar seleção".
- Barra de ações em lote exibindo contagem de itens selecionados.
- Confirmação antes de arquivar ou excluir em massa.

### RF018-03 — Resultado por item, não falha total

Uma ação em massa nunca deve falhar inteiramente por causa de um único item problemático.

Critérios:

- Endpoints bulk retornam `{ requested, succeeded, failed, results: [{ media_id, success, reason? }] }`.
- Cada item é processado independentemente (autorização, checagem de uso, execução).
- A UI exibe um resumo: quantas foram processadas, quantas falharam e por quê.

### RF018-04 — Exclusão em massa respeita dependências

Excluir uma mídia em uso por campanha (via `CampaignPlaylistItem` ou os campos legados `Campaign.media_ids`/`media_order`) deve falhar apenas para aquele item, com motivo claro.

Critérios:

- Checagem de uso cobre **ambos** os caminhos (relacional e legado) — corrigindo uma lacuna que já existia na exclusão individual antes desta SPEC.
- `POST /media/bulk-delete` não tem parâmetro `force` — diferente do `DELETE` individual, uma ação em massa não desvincula campanhas automaticamente.
- Itens bloqueados continuam existindo após a operação; os demais itens do lote são processados normalmente.

### RF018-05 — Arquivamento em massa nunca falha por "em uso"

Arquivar é reversível e não remove a mídia de nenhum lugar — apenas escondendo das seleções futuras — então não há motivo de negócio para bloquear por uso.

Critérios:

- `POST /media/bulk-archive` só falha por item em caso de mídia não encontrada ou sem permissão (tenant).

## Compatibilidade

- `DELETE /media/{id}` individual mantém o comportamento existente (incluindo `force=true` para desvincular campos legados), mas passa a também checar `CampaignPlaylistItem` — bloqueando mesmo com `force=true`, já que isso nunca foi auto-removido.
- Não altera a resolução de campanha do player (`CampaignPlaylistItem`, `backend/api/v1/devices.py`) — fora de escopo, já correto.
- Migration aditiva (`ADD COLUMN archived_at` + novo valor de enum), sem alterar dados existentes.

## Critérios de aceite

- [x] Mídias arquivadas não aparecem por padrão em `GET /media` nem nos seletores de campanha/playlist/agenda.
- [x] UI permite selecionar múltiplas mídias e arquivar/excluir em lote.
- [x] Resultado da ação em massa mostra sucesso/falha por item com motivo.
- [x] Mídia em uso (relacional ou legado) não impede exclusão das demais mídias do lote.
- [x] Arquivamento em massa nunca falha por "em uso".
- [x] `archived_at` sincronizado em qualquer caminho de mudança de status.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
