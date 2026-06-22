# SPEC 012 — Player

Status: aguardando SPEC 011

## Comportamento esperado

Ao receber comando de reinicio:

1. Validar que o comando pertence ao device atual.
2. Confirmar recebimento.
3. Pausar ou silenciar reproducao se necessario.
4. Persistir estado minimo local.
5. Confirmar inicio da execucao.
6. Executar reinicio sem modal.
7. Apos novo boot, restaurar sessao via SPEC 011.
8. Confirmar sucesso quando possivel.

## Estado minimo a preservar

- `device_id`
- `device_token`
- `pairing_code`
- `token_version`
- `pairing_version`
- ultima playlist/config cacheada
- comando em execucao, se for necessario completar ACK apos boot

## Electron

O bridge esperado deve permitir:

```js
window.__ELECTRON__.player.restartApp()
```

Regras:

- Nao abrir prompt.
- Nao depender de clique humano.
- Preferir restart real do app (`app.relaunch()` + `app.quit()`) quando empacotado.
- Em desenvolvimento, pode fazer reload do renderer se documentado.

## Logs minimos

- `PLAYER_COMMAND_RECEIVED`
- `PLAYER_COMMAND_EXECUTING`
- `PLAYER_COMMAND_RESTART_REQUESTED`
- `PLAYER_COMMAND_RESTART_SUCCESS`
- `PLAYER_COMMAND_RESTART_FAILED`

## Checklist de auditoria

- [ ] Conferir `frontend/src/player-core/commands.js`.
- [ ] Conferir `frontend/src/player-core/commandPoller.js`.
- [ ] Conferir `frontend/electron/preload.js`.
- [ ] Conferir `frontend/electron/main.js`.
- [ ] Conferir se restart atual usa prompt ou dialog.
- [ ] Conferir como o player confirma ACK antes/depois da execucao.

