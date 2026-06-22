# SPEC 012 — Design

Status: aguardando SPEC 011

## Fluxo esperado

```text
Gerenciador cria comando restart
  -> Backend grava device_command pending
  -> Player recebe via SSE/polling
  -> Player ACK received
  -> Player salva estado minimo local
  -> Player ACK executing
  -> Player aciona bridge nativo/renderer
  -> App reinicia
  -> SPEC 011 auto boot restaura sessao
  -> Player envia heartbeat
  -> Player/Backend marca comando como success
```

## Decisao importante

Esta SPEC depende diretamente da SPEC 011: se o player nao inicializar sozinho apos o restart, o comando remoto continua exigindo intervencao humana indiretamente.

## Pontos de auditoria obrigatorios

- [ ] Identificar nomes reais dos comandos aceitos pelo backend.
- [ ] Identificar endpoints reais de criar, buscar, receber, iniciar e confirmar comando.
- [ ] Identificar polling/SSE atual do player.
- [ ] Identificar handler do comando de reinicio em `frontend/src/player-core/commands.js`.
- [ ] Identificar bridge Electron em `frontend/electron/preload.js`.
- [ ] Identificar IPC Electron em `frontend/electron/main.js`.
- [ ] Identificar UI do gerenciador que envia comando.
- [ ] Identificar status reais usados pelo banco/backend.

## Arquivos provaveis

- `backend/api/v1/devices.py`
- `backend/core/models.py`
- `backend/core/schemas_completos.py`
- `backend/crud/entidades/crud_device_command.py`
- `frontend/src/api/dispositivos.js`
- `frontend/src/pages/DispositivoDetalhe.jsx`
- `frontend/src/player-core/commandPoller.js`
- `frontend/src/player-core/commands.js`
- `frontend/src/pages/Player.jsx`
- `frontend/electron/preload.js`
- `frontend/electron/main.js`

## Riscos

- Marcar comando como sucesso antes do restart real pode esconder falha.
- Reiniciar antes do ACK pode deixar comando preso em `executing`.
- Se auto boot falhar, restart vira indisponibilidade operacional.
- Usar reload total para tudo pode reiniciar midia/campanha sem necessidade.

