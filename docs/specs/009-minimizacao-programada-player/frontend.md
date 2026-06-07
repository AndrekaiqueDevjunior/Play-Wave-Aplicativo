# SPEC 009 - Frontend Admin

## Tela alvo

`frontend/src/pages/DispositivoDetalhe.jsx`

Adicionar uma secao chamada:

`Comportamento do Player`

## Por que aqui

A funcionalidade e uma politica do dispositivo/player. A tela de detalhe do dispositivo ja concentra:

- comandos remotos;
- historico de comandos;
- plataforma/status;
- acoes administrativas do device.

## Controles

### Comandos manuais

Adicionar botoes:

- `Minimizar`;
- `Restaurar`;
- `Mostrar desktop agora`.

`Mostrar desktop agora` deve abrir/usar input rapido de duracao em segundos ou usar default 5s.

### Cronometro/configuracao

Campos:

- toggle `Ativar rotina`;
- input numerico `Intervalo` em segundos;
- input numerico `Duracao visivel` em segundos;
- switch `Restaurar fullscreen`;
- botao `Salvar`;
- botao `Testar agora`.

Preview:

```text
A cada 20 segundos, mostrar desktop por 5 segundos.
```

## Validacao no frontend

- intervalo minimo: 10s;
- duracao minima: 1s;
- duracao maxima: 300s;
- duracao deve ser menor que intervalo;
- mostrar erro antes de chamar backend.

## API client

Arquivo:

`frontend/src/api/dispositivos.js`

Adicionar:

- `atualizarDesktopExposureConfig(deviceId, payload)`;
- `enviarComando(deviceId, "show_desktop", { payload: { duration_seconds } })`.

## Labels

Arquivo:

`frontend/src/utils/deviceCommands.js`

Adicionar labels:

- `minimize_player: "Minimizar Player"`;
- `restore_player: "Restaurar Player"`;
- `show_desktop: "Mostrar Desktop"`.

## UX de suporte por plataforma

Quando `device.os` ou `player_version` indicar browser/web sem Electron, exibir texto discreto:

```text
Disponivel apenas para Player Electron Windows/Linux no rollout inicial.
```

Nao bloquear o botao necessariamente: deixar enviar pode ser util para registrar ACK `Nao suportado`.

## Estimativa

PR 1 UI comandos manuais: 70-130 linhas.

PR 3 cronometro/config persistente: 160-260 linhas.


