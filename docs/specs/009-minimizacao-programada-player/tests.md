# SPEC 009 - Plano de Testes

## TDD por PR

### PR 1 - Comandos manuais

Escrever primeiro:

- teste backend: `VALID_COMMANDS` aceita `minimize_player`, `restore_player`, `show_desktop`;
- teste backend: comando invalido continua retornando 400;
- teste player: `executeCommand` retorna `UNKNOWN_COMMAND` para comando nao listado;
- teste player: `show_desktop` em web puro retorna `platform_unsupported`.

Depois implementar codigo minimo.

### PR 2 - Config persistente

Escrever primeiro:

- teste backend: PATCH salva config valida;
- teste backend: PATCH rejeita duracao maior/igual ao intervalo;
- teste backend: PATCH rejeita duracao > 300;
- teste backend: device response inclui config com default desligado.

Depois implementar model/schema/migration/endpoint.

### PR 3 - Scheduler e UI

Escrever primeiro:

- teste unitario do scheduler: inicia um timeout;
- teste unitario do scheduler: `stop()` cancela timeout;
- teste unitario do scheduler: config disabled nao agenda;
- teste UI: validacao impede duracao maior que intervalo.

Depois implementar UI e scheduler.

## Testes manuais E2E

### Electron Windows

- enviar `minimize_player`;
- enviar `restore_player`;
- enviar `show_desktop` com 5s;
- validar historico no admin;
- validar que fullscreen volta.

### Electron Linux

- repetir testes Windows;
- validar systemd/kiosk se aplicavel.

### Browser puro

- abrir `/player` no Chrome;
- enviar `show_desktop`;
- validar ACK `failed` com `platform_unsupported=true`.

### Android

- enviar `show_desktop`;
- validar ACK `COMMAND_NOT_IMPLEMENTED` ou documentar comportamento atual.

## Regressao

- comandos antigos continuam funcionando: `sync`, `refresh_playlist`, `restart_app`, `restart_device`, `shutdown_device`;
- SSE `command:new` continua disparando polling imediato;
- Player continua tocando campanha apos restore;
- sem timers duplicados apos reconnect SSE.

## Performance

- verificar que backend nao cria comandos automaticos repetidos para ciclo programado;
- confirmar que so existe um timer local ativo por Player;
- sem aumento de polling.

## Seguranca

- usuario sem permissao no device nao altera config;
- payload fora do range falha;
- browser nao tenta acessar APIs Electron inexistentes.


