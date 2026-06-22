# SPEC 016 — Requirements

Status: implementada
Data: 2026-06-18

## Contexto

Cliente reportou que antes era possível excluir faixas de áudio de verdade, mas agora o sistema "só arquiva" e as faixas continuam aparecendo. A auditoria encontrou que o hard delete já funcionava — o problema real era que faixas arquivadas continuavam aparecendo nos seletores de playlist/rádio/campanha/spots e na listagem padrão do admin, e que a UI não oferecia nenhum caminho para excluir definitivamente nem para restaurar uma faixa arquivada.

## Objetivo

Diferenciar claramente Arquivar / Restaurar / Excluir definitivamente, com faixas arquivadas escondidas por padrão em todas as listagens operacionais, e exclusão definitiva segura (bloqueada quando em uso, com mensagem clara).

## Requisitos funcionais

### RF016-01 — Faixas arquivadas escondidas por padrão

`GET /audio/tracks` não deve retornar faixas com `status=archived` a menos que explicitamente solicitado.

Critérios:

- Novo parâmetro `include_archived` (bool, default `false`).
- Quando `status` é passado explicitamente (ex.: `status=archived`), esse filtro é respeitado independente de `include_archived`.
- Todos os seletores existentes (playlist sonora, rádio, campanha, spots) que já filtravam por `status=active` continuam funcionando sem alteração — o filtro novo só afeta consultas sem `status` explícito.
- A tela de gerenciamento (`FaixasAudio.jsx`) passa `include_archived=true` para continuar permitindo ver/restaurar arquivadas através do filtro de status já existente na UI.

### RF016-02 — Distinção visual entre Arquivar e Excluir definitivamente

A UI deve ter ações visualmente e funcionalmente distintas.

Critérios:

- Botão "Arquivar" (ícone de arquivo) para faixas ativas/inativas — chama `PUT` com `status=archived`.
- Para faixas arquivadas: botão "Restaurar" (volta para `active`) e botão "Excluir definitivamente" (ícone de lixeira, chama `DELETE`).
- Confirmação obrigatória antes de excluir definitivamente, com texto deixando claro que a ação não pode ser desfeita.
- Confirmação antes de arquivar, com texto explicando o efeito (sai das seleções, pode ser restaurada depois).

### RF016-03 — Exclusão definitiva segura

Excluir uma faixa em uso (playlist, pasta de rádio ou spot) deve falhar com mensagem clara, não com erro genérico de banco.

Critérios:

- Endpoint verifica uso em `AudioPlaylistItem`, `AudioFolderTrack` e `AudioSpot` antes de excluir.
- Se em uso, retorna `409 Conflict` com contagem por tipo de referência.
- Se não está em uso, executa a exclusão real (arquivo físico + registro no banco).

### RF016-04 — Timestamp de arquivamento

A faixa deve registrar quando foi arquivada, para exibição futura na UI e auditoria.

Critérios:

- Campo `archived_at` (nullable) no model `AudioTrack`.
- Setado automaticamente ao status mudar para `archived`, limpo ao restaurar — sincronizado independente de qual endpoint foi usado para mudar o status (`PUT` genérico ou `PATCH /status`).
- Exposto em `AudioTrackResponse`.

## Compatibilidade

- Não alterar o comportamento de `status=active`/`status=inactive` explícitos — apenas o caso "sem status filtrado" passa a excluir arquivadas.
- Não alterar o endpoint de resolução de playlist do player (`devices.py`) — já filtrava corretamente.
- Não remover o hard delete real — apenas adicionar a checagem de uso antes dele.
- Migration aditiva (`ADD COLUMN archived_at`), com backfill para faixas já arquivadas antes da migration.

## Critérios de aceite

- [x] Faixas arquivadas não aparecem por padrão em `GET /audio/tracks` nem em nenhum seletor que dependa dele.
- [x] Filtro explícito `status=archived` ou `include_archived=true` continua permitindo ver arquivadas.
- [x] UI distingue visualmente Arquivar, Restaurar e Excluir definitivamente.
- [x] Excluir faixa em uso retorna erro claro (409), não erro genérico de banco.
- [x] Excluir faixa sem uso remove de verdade (arquivo + registro).
- [x] `archived_at` é preenchido/limpo corretamente em ambos os caminhos de mudança de status.
- [ ] Migration aplicada em produção (VPS) — pendente de deploy.
