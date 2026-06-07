# SPEC 009 - Minimizacao Programada do Player

Status: especificacao inicial
Data: 2026-06-01
Projeto: PlayWave

## Objetivo

Permitir que o operador controle remotamente a minimizacao/restauracao do Player e configure uma rotina cronometrada para expor a area de trabalho por alguns segundos, principalmente em players Electron Windows/Linux.

## Contexto

A auditoria `AUDITORIA_MINIMIZACAO_PROGRAMADA_PLAYER.md` confirmou que o PlayWave ainda nao possui comandos remotos de minimizar/restaurar, mas ja tem base reaproveitavel:

- fila persistente `device_commands`;
- endpoints de envio, pending, received, started e ACK;
- SSE `command:new` para reduzir latencia;
- Player React com motor `frontend/src/player-core/commands.js`;
- Electron com `BrowserWindow`, kiosk/fullscreen e IPC.

A feature completa cruza backend, banco, UI admin, Player web, Electron e testes. Se implementada de uma vez, deve passar de 500 linhas de codigo. Por isso a entrega deve ser quebrada em PRs pequenos e testaveis.

## Escopo

Esta SPEC cobre:

- comandos manuais para minimizar, restaurar e mostrar desktop;
- configuracao cronometrada por dispositivo;
- UI admin para configurar intervalo e duracao;
- suporte inicial em Electron Windows/Linux;
- retorno `platform_unsupported` em browser puro, Smart TV web e plataformas sem bridge;
- testes unitarios/backend/player e plano manual E2E.

Esta SPEC nao cobre:

- agente externo Windows Service/Python/Tray para controlar apps fora do Electron;
- suporte robusto Android/Smart TV para minimizar/restaurar Activity;
- regra por campanha ou midia;
- MDM/Device Owner avancado para Android;
- telemetria historica detalhada de cada ciclo de minimizacao.

## Onde implementar

Implementar primeiro em **Dispositivos**.

Motivo:

- minimizar/restaurar e uma politica do hardware/player, nao do conteudo;
- campanhas e midias definem o que tocar, nao como a janela do sistema operacional se comporta;
- o backend ja tem `devices`, `device_commands`, `device.os`, `device.group`, `device.player_version`;
- a tela `DispositivoDetalhe.jsx` ja possui comandos remotos e historico.

Evolucao recomendada:

1. Dispositivo individual: menor risco e melhor para TDD.
2. Tenant/global default: politica padrao para novos dispositivos.
3. Grupo de dispositivos: aplicar em lote por `Device.group`.
4. Nunca acoplar em `campaigns` ou `media`, exceto se uma SPEC futura quiser comportamento especial por campanha com justificativa forte.

## Arquivos analisados

### Backend

- `backend/api/v1/devices.py`
- `backend/core/models.py`
- `backend/core/schemas_completos.py`
- `backend/crud/entidades/crud_device_command.py`
- `backend/services/event_bus.py`
- `backend/alembic/versions/002_add_device_commands.py`
- `backend/alembic/versions/20260521_0915_device_command_lifecycle.py`
- `backend/alembic/versions/20260522_1000_command_defaults_and_index.py`

### Frontend / Player

- `frontend/src/pages/DispositivoDetalhe.jsx`
- `frontend/src/utils/deviceCommands.js`
- `frontend/src/pages/Player.jsx`
- `frontend/src/player-core/commands.js`
- `frontend/src/player-core/platform.js`
- `frontend/electron/main.js`
- `frontend/electron/preload.js`

### Outros

- `backend/compatibilidade_SO/ARQUITETURA.md`
- `backend/compatibilidade_SO/linux/playwave-player.service`
- `backend/compatibilidade_SO/windows/README.md`
- `frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java`

## Estado atual encontrado

### Ja existe

- Comandos remotos persistidos em `device_commands`.
- SSE para avisar `command:new`.
- Player busca comandos pendentes e envia ACK.
- Electron controla fullscreen/kiosk.
- UI admin envia comandos por dispositivo.

### Existe parcialmente

- Electron tem `BrowserWindow.show()` e `setFullScreen()`, mas nao tem IPC de minimizar/restaurar.
- Player tem registry de comandos, mas nao tem handlers de janela.
- Device tem `group`, mas nao existe endpoint de politica por grupo.

### Falta ou precisa consolidar

- command types `minimize_player`, `restore_player`, `show_desktop`.
- configuracao persistente de rotina cronometrada;
- UI de cronometro/intervalo/duracao;
- IPC Electron `window:minimize`, `window:restore`, `window:show_desktop`;
- testes automatizados e manual E2E.

## Requisitos funcionais

### RF009-01 - Comando manual de minimizar

O admin deve conseguir enviar `minimize_player` para um dispositivo.

Criterios:

- backend aceita o comando em `POST /devices/{id}/command`;
- player Electron executa minimizacao da janela;
- player browser puro retorna `platform_unsupported`;
- historico registra status e resultado.

### RF009-02 - Comando manual de restaurar

O admin deve conseguir enviar `restore_player` para um dispositivo.

Criterios:

- backend aceita o comando;
- Electron restaura, exibe, foca e reativa fullscreen/kiosk quando configurado;
- browser puro retorna `platform_unsupported`.

### RF009-03 - Comando mostrar desktop temporario

O admin deve conseguir enviar `show_desktop` com `payload.duration_seconds`.

Criterios:

- Electron minimiza ou tira de fullscreen por N segundos;
- apos N segundos, restaura automaticamente;
- limites: `duration_seconds` entre 1 e 300;
- ACK deve informar plataforma, duracao e timestamps.

### RF009-04 - Configuracao cronometrada por dispositivo

O admin deve configurar por dispositivo:

- `desktop_exposure_enabled`;
- `desktop_exposure_interval_seconds`;
- `desktop_exposure_duration_seconds`;
- `desktop_exposure_restore_fullscreen`;
- `desktop_exposure_updated_at`.

Criterios:

- valores persistem no banco;
- player recebe a configuracao;
- player inicia/para ciclo sem precisar reiniciar app;
- desligar a config cancela timers ativos.

### RF009-05 - Cronometro no frontend admin

A tela do dispositivo deve permitir cronometrar a rotina pelo frontend.

Criterios:

- inputs para intervalo e duracao;
- toggle ativar/desativar;
- preview textual simples: "a cada X segundos, mostrar desktop por Y segundos";
- botao "Testar agora" envia `show_desktop`;
- historico de comandos mostra resultado.

### RF009-06 - Compatibilidade por plataforma

Somente Electron Windows/Linux deve ser considerado suportado no primeiro rollout.

Criterios:

- Electron: executa comandos;
- Web/Smart TV: retorna `platform_unsupported`;
- Android/Capacitor: retorna `COMMAND_NOT_IMPLEMENTED` ate SPEC futura.

## Requisitos nao funcionais

### Codigo

- Entrega em PRs pequenos.
- Cada PR deve ter menos de 500 linhas sempre que possivel.
- Evitar misturar config programada com comandos manuais no mesmo PR inicial.

### Arquitetura

- Reaproveitar `device_commands`.
- Config persistente deve ficar em `devices` inicialmente, com possibilidade de heranca por `tenants` em SPEC futura.
- O ciclo cronometrado deve rodar no Player local, nao no backend.

### Bugs

- Evitar timers duplicados no Player.
- Evitar minimizar em fase de pareamento.
- Evitar restaurar para frente se o comando foi cancelado/desabilitado durante a janela.
- Tratar reconnect SSE sem iniciar multiplos ciclos.

### Seguranca

- Nao permitir que browser puro tente APIs inexistentes de janela.
- Restringir update da config ao mesmo controle de permissao ja usado em `devices.py`.
- Payload de duracao deve ter limites para evitar travar o player fora da tela.
- Nao executar shell para minimizar/restaurar no PR inicial; usar APIs Electron.

### Performance

- Timers locais leves com `setInterval`/`setTimeout`.
- Sem polling adicional no backend.
- SSE existente deve ser reaproveitado para config/command.

### Testes

- TDD: escrever testes antes de implementar cada camada.
- Backend: comandos aceitos/rejeitados e config validada.
- Player: handlers retornam sucesso/unsupported.
- Electron: teste manual E2E obrigatorio em Windows/Linux.

## Decisoes de compatibilidade

- Players antigos ignorarao comandos desconhecidos ou retornarao `UNKNOWN_COMMAND`.
- Backend deve aceitar os novos comandos apenas apos player Electron atualizado no rollout planejado.
- Config nova deve ter defaults desativados para nao mudar comportamento de dispositivos existentes.
- Browser puro deve falhar de forma explicita e auditavel, nao silenciosa.

## Riscos

- Kiosk/alwaysOnTop impedir desktop ficar visivel. Mitigacao: no Electron, desligar fullscreen/alwaysOnTop antes de minimizar e restaurar depois.
- Linux window manager pode variar. Mitigacao: iniciar com APIs Electron, validar em ambiente alvo e so depois considerar `xdotool/wmctrl`.
- Usuario pode configurar intervalo pequeno demais. Mitigacao: limites de validacao.
- Android pode nao permitir restauracao automatica. Mitigacao: fora do escopo inicial.

## Fora de escopo imediato

- Minimizar apps de terceiros.
- Controlar area de trabalho em Smart TVs web.
- Agente instalado como servico do sistema operacional.
- Politica por campanha/midia.

