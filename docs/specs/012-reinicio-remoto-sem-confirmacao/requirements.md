# SPEC 012 — Requirements

Status: aguardando SPEC 011
Data: 2026-06-15

## Contexto

Cliente reportou que, ao enviar comando de reiniciar app/player pelo gerenciador, o comando chega ao player, mas exige confirmacao manual no dispositivo. Em ambiente de loja/TV isso bloqueia operacao remota, porque alguem precisa acessar fisicamente o ponto.

## Objetivo

O comando remoto de reinicio deve reiniciar o player de forma silenciosa, autenticada, rastreavel e sem interacao humana.

## Regra de negocio

Comandos administrativos enviados pelo gerenciador devem ser executados automaticamente pelo player quando:

- foram criados pelo backend;
- pertencem ao dispositivo correto;
- usam token/sessao valida;
- nao estao expirados;
- sao suportados pela plataforma atual.

## Requisitos funcionais

### RF012-01 — Reinicio sem prompt

Ao receber `restart_player` ou comando equivalente existente, o player deve reiniciar sem exibir modal ou confirmacao local.

Criterios:

- Nenhum `confirm()`, `alert()`, dialog nativo ou prompt do Electron bloqueia o fluxo.
- Player salva estado minimo antes de reiniciar.
- Depois do reinicio, player volta para sessao/campanha/playlist anterior quando valida.

### RF012-02 — Ciclo de vida confiavel do comando

O comando deve passar por estados rastreaveis.

Estados esperados:

- `pending`
- `received`
- `executing`
- `success`
- `failed`
- `expired`

Criterios:

- Player confirma recebimento antes de executar.
- Player confirma inicio da execucao.
- Player confirma sucesso ou falha.
- Se o app reiniciar antes do ACK final, deve haver estrategia para registrar sucesso apos boot.

### RF012-03 — Comando idempotente

Enviar o mesmo comando mais de uma vez nao deve deixar o player em loop permanente.

Criterios:

- Comandos ja executados nao sao executados novamente.
- Comando duplicado tem resultado previsivel.
- Retry controlado nao reinicia infinitamente.

### RF012-04 — Bridge nativo sem confirmacao

Electron/Windows deve executar restart silencioso.

Criterios:

- `restart_app` ou equivalente usa mecanismo nativo/renderer sem prompt.
- Se usar `app.relaunch()` + `app.quit()`, o ACK de inicio precisa ser enviado antes.
- Se usar `window.location.reload()`, nao pode perder estado nem quebrar cache.

### RF012-05 — Feedback no gerenciador

Gerenciador deve mostrar status real do comando.

Criterios:

- Usuario ve comando como pendente, em execucao, concluido ou falho.
- Falhas exibem motivo.
- Nao fica eternamente em "enviado".

## Compatibilidade

- Reaproveitar comandos existentes se ja houver `restart_app`, `restart_player`, `reload_player` ou equivalente.
- Nao quebrar comandos de `shutdown_device`, `restart_device`, `sync`, `clear_cache`.
- Se o backend usa `completed` em vez de `success`, documentar e preservar o contrato real.

## Criterios de aceite

- [ ] Ao clicar em reiniciar no gerenciador, o player reinicia sem confirmacao manual.
- [ ] O comando muda de `pending` para estado final de sucesso.
- [ ] O player volta para campanha/playlist anterior.
- [ ] Nenhum modal bloqueia a reproducao.
- [ ] O log do dispositivo mostra horario e resultado do comando.
- [ ] Falha de plataforma retorna erro claro.

