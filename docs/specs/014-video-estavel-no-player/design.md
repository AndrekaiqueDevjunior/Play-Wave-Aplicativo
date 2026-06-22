# SPEC 014 — Design

Status: implementada

## Fluxo esperado (preload)

```text
Player.jsx calcula `current` (playlist[currentIndex]) e `nextMedia`
  (playlist[(currentIndex+1) % length]) — ambos ja existiam, nextMedia so
  nao era usado para nada alem do overlay de debug.
  -> <MediaRenderer media={current} nextMedia={nextMedia} ... />
  -> MediaRenderer renderiza:
       - conteudo visivel de `media` (video/img/iframe/audio), como antes
       - <MediaPreloader media={nextMedia} /> — elemento oculto
         (position absolute, width/height 0, opacity 0) do mesmo tipo,
         com a mesma URL resolvida
  -> Navegador comeca a buscar/decodificar o arquivo de `nextMedia` em
     paralelo, usando o cache HTTP normal (Range requests, Cache-Control
     ja suportados pelo backend)
  -> Quando a midia avanca (advanceMedia), `current` passa a ser o que era
     `nextMedia` — o navegador ja tem (ou esta terminando de baixar) o
     arquivo, reduzindo o tempo de buffering inicial
  -> Novo `nextMedia` e calculado, novo preload e criado
```

## Fluxo esperado (memoizacao)

```text
Player.jsx atualiza estado nao relacionado a midia (heartbeat 30s,
spot tick 5s, radio resolver 60s, progress 250ms)
  -> Player.jsx re-renderiza (function component invocada de novo)
  -> JSX de <MediaRenderer media={current} nextMedia={nextMedia} ... />
     e recriado, mas com as MESMAS referencias de objeto (current/nextMedia
     sao lookups em array que nao mudam de identidade) e mesmos callbacks
     (advanceMedia/handleMediaError sao useCallback memoizados)
  -> React.memo(MediaRenderer) compara props (shallow equal) -> iguais
  -> React PULA a re-execucao do corpo de MediaRenderer inteiramente:
     sem recalcular renderContent(), sem re-avaliar JSX do <video>,
     sem re-rodar os useEffect/useCallback internos
  -> Quando `progress` muda (250ms) ou `media`/`nextMedia` mudam de fato,
     o memo deixa passar e MediaRenderer re-renderiza normalmente
  -> Dentro de MediaRenderer, a barra de progresso usa um useEffect que
     escreve `style.width` direto no DOM via ref — não depende de
     renderContent() ser re-executado para se atualizar
```

## Decisao tecnica: por que nao usar `<link rel="preload">`

A alternativa mais "padrao web" seria `<link rel="preload" as="video" href={...}>` no `<head>`. Foi descartada porque:

- `as="video"` ainda tem suporte inconsistente entre engines/Electron versions usadas no parque de dispositivos do cliente (mistura de Windows/Electron, Android/Capacitor, SmartTV).
- Gera warning de "preloaded but not used" no console quando o item e pulado/trocado antes da vez (ex: comando de skip, troca de campanha) — poluiria os logs de diagnostico que o player ja usa ativamente (`PLAYER_VIDEO_DEBUG`).
- Um elemento real (`<video>`/`<img>`/`<audio>` oculto) da o mesmo resultado pratico (arquivo entra no cache HTTP do browser) com comportamento mais previsivel entre plataformas, e sem exigir await/cleanup de tags no `<head>`.

## Decisao tecnica: memo com comparador padrao (shallow), nao customizado

A primeira tentativa de implementacao usou um comparador customizado que excluia `progress` da comparacao, para tentar eliminar os 4 re-renders/segundo do `MediaRenderer`. Essa abordagem foi descartada depois do teste automatizado falhar: quando `React.memo` decide que as props sao "iguais" (segundo o comparador), **o componente nem chega a re-executar** — logo o `useEffect` que atualiza a barra de progresso via ref nunca roda, e a barra trava.

A barra de progresso depende de `progress` mudar e o componente re-renderizar para o `useEffect` correspondente disparar. Por isso o memo final usa o comparador **padrao** do `React.memo` (shallow equal em todas as props, incluindo `progress`) — o ganho real nao vem de ignorar `progress`, vem de pular re-renders quando **nenhuma prop muda**, o que cobre o caso real do diagnostico: re-renders do `Player.jsx` disparados por estado de audio/spot/radio que nao tocam em `media`/`nextMedia`/`progress`.

## Pontos de auditoria realizados

- [x] Confirmar key={media.id} no `<video>` — necessario para troca real de conteudo, nao e a causa do bug.
- [x] Confirmar ausencia de preload-next-media em `Player.jsx`/`MediaRenderer.jsx`.
- [x] Confirmar suporte a Range Requests no backend (`backend/main.py:137-174`) — ja adequado.
- [x] Confirmar metadata de video no model `Media` (ffprobe) — duration/resolution/has_audio presentes; bitrate/fps ausentes como coluna dedicada mas presentes em `extra_metadata`.
- [x] Confirmar ausencia de flags de hardware acceleration no Electron — sem regressao (Electron habilita por padrao).
- [x] Confirmar ausencia de `window.location.reload()` no caminho de execucao normal do player.
- [x] Confirmar logging de eventos de video ja existente e completo (`VIDEO_EVENTS` em `MediaRenderer.jsx`).
- [x] Confirmar frequencia de re-render do `Player.jsx` (progress 250ms, heartbeat 30s, spot tick 5s, radio resolver 60s) sem memoizacao do componente de video.

## Arquivos impactados

- `frontend/src/components/player/MediaRenderer.jsx` — `MediaPreloader`, `React.memo`, barra de progresso via ref.
- `frontend/src/pages/Player.jsx` — passa `nextMedia` para os dois call sites de `<MediaRenderer>`.
- `frontend/src/__tests__/media_renderer.test.jsx` — testes novos (preload + memo).

Nao foram necessarias mudancas em:

- `backend/main.py` / `backend/api/v1/media.py` — entrega de midia e metadata ja adequadas.
- `frontend/electron/main.js` — sem flag de GPU para remover/ajustar.
- `frontend/src/pages/CampanhaPreview.jsx` — preview do gerenciador fora de escopo (ja funciona).

## Riscos

- Preload de videos grandes consome banda mesmo quando o item nunca chega a tocar (ex: pulado por comando remoto antes da vez) — aceitavel: e exatamente o mesmo arquivo que tocaria a seguir na sequencia normal, o desperdicio so ocorre em trocas fora do fluxo padrao (raras).
- Em dispositivos com poucos recursos, ter 2 elementos `<video>` simultaneos (1 visivel + 1 oculto em preload) pode aumentar uso de memoria/decodificacao. Mitigado: o preload usa `preload="auto"` mas fica oculto (sem `autoplay`), entao nao decodifica frames ativamente — apenas baixa o arquivo. Pendente validar em hardware real de loja.
- A memoizacao depende de `current`/`nextMedia` manterem identidade de objeto estavel (`playlist[index]`) e dos callbacks serem `useCallback` — se uma futura alteracao em `Player.jsx` recriar esses objetos/funcoes a cada render, o ganho do memo desaparece silenciosamente (sem erro, so volta ao comportamento anterior). Vale um teste de regressao se o `Player.jsx` for refatorado.
