# SPEC 015 — Tests

Status: implementada — testes unitarios de frontend passando; testes de backend validados por sintaxe (pytest nao executavel neste ambiente); validacao em hardware pendente

## Testes automatizados — Frontend (executados)

### `contentGuard` (`frontend/src/__tests__/content_guard.test.js`)

| Teste | Resultado |
|---|---|
| Nao esta ocupado por padrao (estado inicial) | passou |
| Fica ocupado quando phase=playing e ha playlist | passou |
| Nao fica ocupado em outras fases mesmo com playlist | passou |
| Nao fica ocupado quando playing mas sem playlist (so radio) | passou |
| Chama o callback imediatamente quando nao ha conteudo ativo | passou |
| Represa o callback até notifyContentEnded quando ha conteudo ativo | passou |
| Dispara apenas uma vez mesmo que notifyContentEnded seja chamado de novo | passou |
| Dispara multiplos callbacks registrados na mesma janela | passou |
| A funcao de cancelamento remove o callback antes do disparo | passou |
| Um erro em um callback nao impede os demais de disparar | passou |
| Retorna null quando nao ha conteudo ativo (getRemainingMs) | passou |
| Retorna null quando endsAt e desconhecido (duracao natural) | passou |
| Calcula o tempo restante em ms quando endsAt e conhecido | passou |
| Nunca retorna negativo quando endsAt ja passou | passou |

Comando: `npx vitest run src/__tests__/content_guard.test.js` — `14 passed (14)`.

### `windowExposureScheduler` (`frontend/src/__tests__/window_exposure_scheduler.test.js`)

| Teste | Resultado |
|---|---|
| Nao agenda quando desktop exposure esta desabilitado (pre-existente) | passou |
| Agenda e executa show_desktop quando habilitado no Electron (pre-existente) | passou |
| Nao agenda fora do Electron (pre-existente) | passou |
| Com contentGuard e conteudo ativo, espera o fim antes de executar show_desktop | passou |
| Com contentGuard e sem conteudo ativo, executa imediatamente no intervalo | passou |
| Dispara onWarning quando show_warning esta ativo na config | passou |
| stop() cancela a espera por fim de conteudo pendente | passou |

Comando: `npx vitest run src/__tests__/window_exposure_scheduler.test.js` — `7 passed (7)`.

### `desktopExposureTimeScheduler` (`frontend/src/__tests__/desktop_exposure_time_scheduler.test.js`)

13 testes pre-existentes (nextOccurrence, computeNext, agendamento, recover()) + 5 novos:

| Teste novo | Resultado |
|---|---|
| Sem contentGuard, mantem o comportamento antigo (minimiza no horario exato) | passou |
| Com contentGuard e conteudo ativo, espera onceContentEnd antes de minimizar | passou |
| Com contentGuard e sem conteudo ativo, minimiza imediatamente no horario | passou |
| Dispara onWarning antes de esperar o fim do conteudo quando show_warning ativo | passou |
| stop() cancela a espera por fim de conteudo pendente | passou |

Comando: `npx vitest run src/__tests__/desktop_exposure_time_scheduler.test.js` — `18 passed (18)`.

### Suites relacionadas (sem regressao)

```bash
npx vitest run src/__tests__/content_guard.test.js src/__tests__/window_exposure_scheduler.test.js \
  src/__tests__/desktop_exposure_time_scheduler.test.js src/__tests__/window_commands.test.js \
  src/__tests__/media_renderer.test.jsx src/__tests__/audio_manager.test.js
```

Resultado: `79 passed (79)`.

### Suite completa do frontend

```bash
npx vitest run
```

Resultado: `170 passed`, `3 failed` — todos pre-existentes e nao relacionados (confirmados em SPECs anteriores via `git stash`): `player_sse.test.js` (parse error de JSX em arquivo `.test.js`) e `playbackQueueManager.test.js` (3 testes, arquivo nao tocado por esta SPEC).

### Lint

```bash
npx eslint src/pages/Player.jsx src/player-core/contentGuard.js \
  src/player-core/windowExposureScheduler.js src/player-core/desktopExposureTimeScheduler.js \
  src/pages/DispositivoDetalhe.jsx
```

Resultado: 0 erros novos. Warnings remanescentes (`videoMuted` nao usado, `device`/`syncLog`/`error`/`refetchCommands` nao usados) confirmados pre-existentes via `git diff --stat` (linhas nao tocadas nesta SPEC).

## Testes automatizados — Backend (validados por sintaxe, nao executados)

`backend/tests/test_device_desktop_exposure_config.py` — testes novos:

- `test_desktop_exposure_config_defaults_disabled_for_old_device` (estendido com os campos de aviso).
- `test_desktop_exposure_config_exposes_warning_fields_when_set`.
- `test_update_desktop_exposure_config_persists_warning_fields`.
- `test_desktop_exposure_warning_seconds_before_out_of_range_rejected`.

Mais os 4 testes pre-existentes preservados sem alteracao de logica.

Tentativa de execucao real:

```bash
cd backend && python3 -m pytest tests/test_device_desktop_exposure_config.py -q
```

Resultado: `ModuleNotFoundError: No module named 'fastapi'` — o ambiente de desenvolvimento local nao tem as dependencias do backend instaladas (sem venv do projeto, sem fastapi/sqlalchemy/etc. no Python do sistema). Mesma limitacao ja registrada nas SPECs 011-014.

Mitigacao aplicada: validacao de sintaxe de todos os arquivos Python alterados via `ast.parse`:

```bash
python3 -c "
import ast
for f in ['tests/test_device_desktop_exposure_config.py', 'alembic/versions/20260618_1100_desktop_exposure_warning.py', 'core/models.py', 'core/schemas_completos.py', 'api/v1/devices.py']:
    ast.parse(open(f).read()); print('OK:', f)
"
```

Resultado: `OK` para os 5 arquivos. Complementado por revisao manual linha a linha de cada teste e do endpoint alterado.

## Testes manuais sugeridos (nao executados nesta SPEC)

### TM015-01 — Minimizacao espera fim do video

Pre-condicao: device Electron com `desktop_exposure_enabled=true`, `interval_seconds` curto (ex.: 60s), playlist com um video de varios minutos.

Passos:

1. Iniciar reproducao do video.
2. Aguardar o intervalo configurado passar enquanto o video ainda toca.
3. Observar console: deve aparecer `[windowExposureScheduler] conteúdo ativo — aguardando fim antes de minimizar`.
4. A janela NAO deve minimizar nesse momento.
5. Aguardar o video terminar (ou avancar para o proximo item da playlist).
6. A janela deve minimizar imediatamente apos o termino.

Resultado esperado: nenhum corte de conteudo, minimizacao ocorre exatamente na transicao entre midias.

### TM015-02 — Aviso visual aparece antes de minimizar

Pre-condicao: mesma config do TM015-01, com `show_warning=true`, `warning_seconds_before=15`, `warning_text="Voltamos já"`.

Passos:

1. Repetir TM015-01.
2. No momento em que a minimizacao seria represada, observar o overlay "Voltamos já" no rodape do player.
3. O overlay deve permanecer visivel por pelo menos 15 segundos (ou até a minimizacao acontecer, o que for mais tarde).

Resultado esperado: aviso visivel, texto correto, sem bloquear a reproducao do conteudo atual.

### TM015-03 — Sem conteudo ativo, minimiza sem demora

Pre-condicao: device com campanha sem midia visual (apenas radio) ou tela "aguardando campanha".

Passos: aguardar o intervalo/horario configurado.

Resultado esperado: minimiza imediatamente, sem espera (log do scheduler nao deve mencionar "aguardando fim").

### TM015-04 — Configuracao via gerenciador

Passos: abrir `DispositivoDetalhe.jsx`, marcar "Exibir aviso antes de minimizar", configurar segundos e texto, salvar.

Resultado esperado: PATCH bem-sucedido, valores refletidos apos reload da pagina (busca novamente o device).

## Evidencias de teste

- Ambiente: desenvolvimento local (Vitest, jsdom, fake timers para os schedulers).
- Build/commit: branch `fix/dev-env`.
- Arquivos alterados: ver `tasks.md`/`design.md` para lista completa.
- Data: 2026-06-18.
- Resultado: 79/79 testes novos+relacionados de frontend passando; 170/173 na suite completa (3 falhas pre-existentes); backend validado por sintaxe (pytest indisponivel no ambiente).
- Observacoes: validacao manual em hardware Windows real (TM015-01 a TM015-04) e deploy da migration na VPS ficam pendentes, mesma situacao registrada nas SPECs anteriores para itens que exigem ambiente fisico/producao.
