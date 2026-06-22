# SPEC 012 — Reinicio Remoto sem Confirmacao

Status: aguardando SPEC 011
Data: 2026-06-15
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md`

## Objetivo

Garantir que o comando remoto de reiniciar app/player seja executado automaticamente pelo player, sem modal, prompt nativo ou clique humano no dispositivo.

## Regra de sequenciamento

Esta SPEC so deve entrar em implementacao depois que a `SPEC 011 — Player Auto Boot` estiver concluida com criterios de aceite validados.

Pode haver diagnostico antecipado compartilhado com a SPEC 011 em:

- storage/sessao do player;
- heartbeat;
- comandos remotos;
- bridge Electron;
- fluxo de reinicio e retorno ao player.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho tecnico e fluxo do comando.
- `api-contract.md` — ciclo de vida esperado de comandos.
- `player.md` — comportamento no player/Electron.
- `tasks.md` — backlog executavel.
- `tests.md` — plano de testes.

## Fora de escopo

- Implementar shutdown/reboot fisico completo do sistema operacional, exceto se ja existir no bridge atual e for necessario para compatibilidade.
- Redesenhar a tela de dispositivos.
- Resolver todos os comandos administrativos.
- Corrigir auto boot. Isso pertence a SPEC 011.

