# SPEC 016 — Faixas de Áudio: Arquivar/Restaurar/Excluir

Status: implementada — testes de frontend passando; testes de backend validados por sintaxe (pytest não executável neste ambiente); deploy/migration pendente
Data: 2026-06-18
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-003)

## Objetivo

Diferenciar claramente Arquivar / Restaurar / Excluir definitivamente para faixas de áudio, garantindo que faixas arquivadas não apareçam em nenhuma listagem operacional (seletor de playlist/rádio, lista padrão do admin) por padrão, e que a exclusão definitiva seja segura (bloqueada com mensagem clara quando a faixa está em uso).

## Regra de sequenciamento

Esta SPEC entrou em implementação após a `SPEC 015 — Minimizar Windows sem Cortar Conteúdo` ser concluída (79/79 testes de frontend passando).

## Diagnóstico resumido

Diferente do que o relato do cliente sugeria ("antes dava para excluir, agora só arquiva"), a auditoria encontrou que:

- **Excluir já fazia hard delete de verdade** (`DELETE /audio/tracks/{id}` chama `crud_audio_track.remove()`, que executa `db.delete()` real) — não era um bug de "exclusão fake".
- **O bug real era de leak de filtro**: arquivar funcionava (`status = "archived"`), mas a listagem padrão (`GET /audio/tracks`, usada por `listarFaixas()` em todo o frontend — seletor de playlist, seletor de rádio, campanhas, spots, e a própria tela de gerenciamento) não excluía faixas arquivadas. Só o endpoint de resolução de playlist do player (`backend/api/v1/devices.py`) já filtrava corretamente por `status == "active"`.
- **Excluir definitivamente não tinha proteção**: as 3 tabelas que referenciam `AudioTrack` (`AudioPlaylistItem`, `AudioFolderTrack`, `AudioSpot`) usam `ondelete="RESTRICT"` — ou seja, excluir uma faixa em uso já falhava no banco, mas com um `IntegrityError` genérico (500), sem mensagem clara para o usuário.
- **A UI da tela de gerenciamento não distinguia Arquivar de Excluir**: o botão de lixeira chamava `atualizarFaixa(id, { status: "archived" })` — ou seja, "Excluir" na UI sempre arquivava, e não havia nenhum caminho de UI para excluir definitivamente nem para restaurar uma faixa arquivada individualmente.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho técnico do filtro padrão, archived_at e checagem de uso.
- `api-contract.md` — contrato de `GET /audio/tracks` (campo novo `include_archived`) e `DELETE /audio/tracks/{id}` (novo erro 409).
- `player.md` — confirmação de que o player já estava correto (sem mudança necessária).
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidências.

## Fora de escopo

- Padronizar `deleted_at` (soft delete via timestamp de exclusão) — esta SPEC manteve o hard delete real já existente; `deleted_at` fica para a `SPEC 020 — Padrão Arquivamento vs Exclusão`, que é dedicada a unificar o padrão em todos os recursos (faixas, playlists, mídias).
- Aplicar o mesmo padrão de filtro/checagem de uso a Playlist Sonora — isso é o objetivo da `SPEC 017`.
- Migration aplicada em produção (VPS) — pendente de deploy, mesma situação das SPECs anteriores.
