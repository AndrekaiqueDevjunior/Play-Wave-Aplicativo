# SPEC 013 — Spot da Radio sem Sobreposicao

Status: implementada — diagnostico e correcao concluidos, testes automatizados passando
Data: 2026-06-17
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-006)

## Objetivo

Garantir que o spot da radio nunca toque por cima da musica do player, respeitando a politica de insercao configurada (`interrupt`, `wait_silence`, `fade_mix`).

## Regra de sequenciamento

Esta SPEC entrou em implementacao apos a `SPEC 012 — Reinicio Remoto sem Confirmacao` ser concluida (11/11 e 12/12 testes Playwright passando).

## Diagnostico resumido

O campo `insertion_policy` ja existia no backend (`AudioSpotInsertionPolicy`: `interrupt`, `wait_silence`, `fade_mix`) e no player (`audioManager.js playSpot()`), mas o modo `wait_silence` nao implementava o comportamento que o nome sugere: ele apenas fazia fade-out do fundo e tocava o spot imediatamente, igual ao `interrupt`. Isso reproduzia exatamente o bug relatado pelo cliente — o spot podia comecar enquanto a musica ainda estava audivel, misturando o som durante o fade.

Nao foi necessario alinhar os nomes do enum com o documento original (`WAIT_TRACK_END`/`INTERRUPT_WITH_FADE`/`DUCKING`/`IMMEDIATE`) — os nomes atuais (`wait_silence`/`interrupt`/`fade_mix`) ja cobrem a mesma semantica e renomear exigiria migration sem ganho funcional.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho tecnico e fluxo do lock de audio.
- `api-contract.md` — contrato de `insertion_policy` (sem mudanca de schema).
- `player.md` — comportamento no AudioManager/player.
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidencias.

## Fora de escopo

- Renomear enum `AudioSpotInsertionPolicy` para os nomes do documento original.
- Implementar `IMMEDIATE` como politica separada (o player ja suporta tocar imediatamente via `interrupt`).
- Resolver sobreposicao entre spot e audio de **video/campanha** (`media_audio`) — o bug relatado e especificamente radio x spot. `media_audio` ja pausa quando ha spot tocando (guard existente em `playMediaAudio`).
- SPEC 014 (Video Estavel no Player) — depende desta SPEC estar concluida.
