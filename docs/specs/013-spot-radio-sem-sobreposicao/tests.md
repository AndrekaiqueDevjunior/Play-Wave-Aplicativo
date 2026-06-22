# SPEC 013 — Tests

Status: implementada — testes unitarios passando, teste manual/hardware pendente

## Testes automatizados (executados)

Arquivo: `frontend/src/__tests__/audio_manager.test.js`

| Teste | Resultado |
|---|---|
| `playSpot(url, 'interrupt')` emite `current = AUDIO_STATE.SPOT` | passou (pre-existente) |
| `'interrupt'` toca o spot imediatamente mesmo com a musica ainda audivel | passou |
| `'wait_silence'` NAO toca o spot por cima da musica ativa — represa como `_pendingSpot` | passou |
| `'wait_silence'` toca o spot represado quando a musica atual emite `'ended'` | passou |
| `'wait_silence'` toca o spot imediatamente quando o fundo ja esta em silencio (pausado) | passou |
| `'fade_mix'` toca o spot imediatamente e reduz volume do fundo (ducking) | passou |
| `nunca toca spot e musica simultaneamente`: `'wait_silence'` com fundo pausado toca direto | passou |

Comando executado:

```bash
cd frontend && npx vitest run src/__tests__/audio_manager.test.js
```

Resultado: `29 passed (29)`.

Suites relacionadas (sem regressao):

```bash
npx vitest run src/__tests__/audio_conflict_resolver.test.jsx src/__tests__/spotScheduleResolver.test.js src/__tests__/osd_audio_player.test.jsx
```

Resultado: `17 passed (17)`. (`player_sse.test.js` falha ao parsear devido a JSX em arquivo `.test.js` — falha pre-existente, nao relacionada a esta SPEC, confirmada via `git status` sem alteracoes nesse arquivo.)

## Testes manuais sugeridos (nao executados nesta SPEC)

### TM013-01 — Spot aguarda fim da musica (hardware real)

Pre-condicao: player Electron rodando com playlist de radio e spot configurado com `wait_silence` e `interval_seconds` curto.

Passos:

1. Iniciar reproducao de uma faixa de radio.
2. Aguardar o spot ficar elegivel enquanto a faixa ainda esta tocando.
3. Ouvir/observar: o spot NAO deve comecar ate a faixa atual terminar.
4. Verificar console: deve aparecer `[AudioManager] SPOT_QUEUED`.
5. Ao terminar a faixa, o spot deve tocar sozinho, sem sobreposicao.
6. Apos o spot, a proxima faixa da radio deve tocar (nao a mesma que acabou).

Resultado esperado: nenhuma sobreposicao audivel, spot toca no intervalo entre musicas.

### TM013-02 — Politica `interrupt` continua imediata

Passos: configurar spot com `interrupt`, aguardar elegibilidade durante musica tocando.

Resultado esperado: musica faz fade-out, spot toca, musica retoma — sem esperar o fim da faixa (comportamento inalterado).

### TM013-03 — Politica `fade_mix` continua com ducking

Passos: configurar spot com `fade_mix`, aguardar elegibilidade durante musica tocando.

Resultado esperado: musica continua audivel em volume reduzido durante o spot (comportamento inalterado).

## Evidencias de teste

- Ambiente: desenvolvimento local (Vitest, jsdom mocks de `<audio>`).
- Build/commit: branch `fix/dev-env`, alteracoes em `frontend/src/lib/audioManager.js` e `frontend/src/__tests__/audio_manager.test.js`.
- Data: 2026-06-17.
- Resultado: 29/29 testes unitarios do `AudioManager` passando; 17/17 testes relacionados sem regressao.
- Observacoes: validacao de audio fisico (TM013-01/02/03) depende de hardware real e nao foi executada nesta sessao.
