# SPEC 010 — Frontend Admin

## Nova seção em `DispositivoDetalhe.jsx`: "Exposição de Desktop (por horário)"

Separada da seção de exposição por intervalo (SPEC 009).

### Lista de eventos
- Tabela/lista com: Nome · Horário (HH:MM) · Duração (s) · Ativo (toggle) · ações (editar/remover).
- Estado vazio: "Nenhum horário configurado."

### Formulário (criar/editar)
- `name` — input texto (1–120).
- `time` — input `type="time"` (HH:MM).
- `duration_seconds` — input número (1–300) com sufixo "segundos".
- `enabled` — switch.
- (Opcional) `weekdays` — seletor de dias da semana; vazio = todos os dias.
- Botões: **Salvar** / **Cancelar**. Edição inline ou dialog (reusar `components/ui/dialog`).

### Ações
- "Adicionar horário" → POST.
- Editar → PATCH.
- Remover → DELETE (com confirmação).
- Toggle Ativo → PATCH `{ enabled }`.

### Preview
- Texto de apoio: "Às **08:00**, o player minimiza por **15s** e volta sozinho à tela cheia."

## API client — `frontend/src/api/`
Adicionar funções (axios `apiClient`):
- `listDesktopExposureEvents(deviceId)`
- `createDesktopExposureEvent(deviceId, payload)`
- `updateDesktopExposureEvent(deviceId, eventId, payload)`
- `deleteDesktopExposureEvent(deviceId, eventId)`

## Componentes reutilizados
- `components/ui/` (button, input, switch, dialog, table) — shadcn/ui já presente.
- Padrão de chamada/erro/toast igual ao da seção de exposição por intervalo.
