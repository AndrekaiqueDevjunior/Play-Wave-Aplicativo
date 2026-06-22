# SPEC 011 — Player Auto Boot

Status: implementacao parcial
Data: 2026-06-15
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md`

## Objetivo

Garantir que o player de loja/TV inicialize sozinho em modo operacional, sem modal de escolha manual, quando existir sessao valida, codigo de pareamento salvo ou configuracao local suficiente para operar offline.

## Regra de sequenciamento

Esta SPEC e a primeira da fila critica de junho. A proxima SPEC da fila so deve entrar em implementacao depois que esta estiver:

- diagnostico preenchido com arquivos reais;
- implementacao concluida;
- testes manuais principais executados;
- criterios de aceite marcados;
- riscos e pendencias registrados.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — fluxo tecnico esperado.
- `api-contract.md` — endpoints necessarios ou a validar.
- `player.md` — comportamento do player no boot.
- `tasks.md` — backlog executavel.
- `tests.md` — plano de testes.

## Diagnostico resumido

- O modal "Manter sessão atual" / "Apagar e começar do zero" esta em `frontend/electron/main.js`, dentro de `handleSessionOnStartup()`.
- O React Player ja pula a tela de pareamento quando `PairingStorage` contem `device_id` e `device_token`.
- O preload do Electron ja suporta credenciais pre-pareadas via `frontend/electron/config.json`.
- O storage do player ja possui `PairingStorage`, `PlaylistCache` e `PlayerState`.
- O backend ja possui heartbeat em `POST /devices/{device_id}/heartbeat`, atualizando `last_seen_at`, `status`, `player_version`, `ip_address` e `storage_used`.
- A primeira implementacao deve focar em eliminar a decisao manual do Electron em producao/kiosk e preservar sessao/cache valido.
- Implementacao parcial realizada em `frontend/electron/main.js`: `AUTO_BOOT` preserva storage e pula o modal nativo em kiosk/producao.

## Fora de escopo

- Redesenhar a tela de pareamento.
- Recriar toda a arquitetura de player.
- Corrigir comandos remotos de restart. Isso fica para a SPEC seguinte.
- Corrigir spots, video travando, minimizacao Windows ou exclusao de midias.
