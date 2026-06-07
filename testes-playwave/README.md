# testes-playwave — Suíte E2E do PlayWave

Testes **positivos, reais** (API + UI) com foco na arquitetura de **Scheduler/Fila**.
Sem mocks de backend: tudo cria dado real e valida no banco/back/player.

## Pré-requisitos

A stack precisa estar no ar:
- **Backend FastAPI** (ex: `http://127.0.0.1:8000`) + **PostgreSQL** + **Redis**
- **Painel** (Vite) servindo em `http://127.0.0.1:3100` (para os testes `@ui`)
- Usuário admin existente (ver `backend/.env` → `ADMIN_INITIAL_EMAIL/PASSWORD`)

> Os testes `@api` (maioria, incluindo a fila) **não** precisam do painel — só do backend.
> Os testes que tocam o player real exigem `RUN_PLAYER_API=true` (default).

## Setup

```bash
cd testes-playwave
cp .env.example .env          # ajuste API_URL, WEB_URL, ADMIN_EMAIL, ADMIN_PASSWORD
npm install
npx playwright install        # baixa os browsers (necessário p/ testes @ui)
```

## Rodar

```bash
npx playwright test                 # tudo
npm run test:fila                   # só o core (scheduler-fila)
npx playwright test --grep @api     # só API (não precisa do painel)
npx playwright test --grep @ui      # só UI
npx playwright test --grep @sse     # só os de SSE/tempo real
```

## Relatório

```bash
npx playwright show-report reports/html
```

- HTML em `reports/html`, JSON em `reports/results.json`.
- **Trace** e **vídeo** retidos só em falha (`reports/artifacts/`).
- **Screenshot** só em falha.

## Estrutura

```
testes-playwave/
├── playwright.config.ts      # serial (workers=1), html+json, trace/screenshot/video on-failure
├── .env.example
├── tsconfig.json
├── helpers/
│   ├── env.ts                # config + uniqueName()
│   ├── api.ts                # Api client aterrado nos endpoints REAIS
│   ├── auth.ts               # login UI + seed de storage
│   ├── media-gen.ts          # WAV de silêncio válido (duração real p/ ffprobe)
│   ├── factories.ts          # builders: tracks, pastas, playlists, spots, campanhas
│   ├── sse.ts                # cliente SSE (não há WebSocket no backend)
│   └── cleanup.ts            # Tracker de teardown (LIFO, best-effort)
├── fixtures/
│   ├── test-fixtures.ts      # fixtures: api(admin) + tracker(auto-cleanup)
│   └── media/                # coloque sample.mp4 aqui p/ habilitar testes de vídeo
├── tests/
│   ├── auth.setup.ts         # login 1x → storageState
│   ├── scheduler-fila.spec.ts   ← CORE
│   ├── upload-multiplo.spec.ts
│   ├── categorias.spec.ts
│   ├── pastas-audio.spec.ts
│   ├── spots.spec.ts
│   ├── radio-playlists.spec.ts
│   ├── campanhas.spec.ts
│   ├── player.spec.ts
│   ├── dispositivos-comandos.spec.ts
│   ├── debug.spec.ts
│   └── electron-windows.spec.ts
├── CHECKLIST_TESTES.md
└── RELATORIO_FINAL.md        # data-testid faltantes, endpoints, gaps da fila, recomendações
```

## Notas importantes

- **Sem `data-testid` no painel** (auditado: 0). Os testes são **API-first**; os `@ui`
  são smokes por role/texto. Lista de `data-testid` a criar em `RELATORIO_FINAL.md`.
- **Sem WebSocket**: tempo real é **SSE** (`/devices/{id}/playlist/updates`) + polling.
- Partes exclusivamente client-side do player (ordem de shuffle, OSD, no-reload,
  janela Electron) ficam como `test.fixme()` apontando os testes de componente já
  existentes em `frontend/src/__tests__/`.
