# ✅ Checklist de Testes — PlayWave E2E

Marcação reflete **teste criado nesta suíte** (não o status do produto).
Legenda: `[x]` teste real implementado · `[~]` parcial (parte via API, parte `test.fixme`) · `[ ]` pendente (`test.fixme` com motivo).

| # | Item | Status | Arquivo | Observação |
|---|------|--------|---------|------------|
| 01 | Upload múltiplo | [x] | `tests/upload-multiplo.spec.ts` | upload em lote + disponibilidade em playlist |
| 02 | Categorias personalizadas | [x] | `tests/categorias.spec.ts` | API ✓; drawer UI = smoke (falta data-testid) |
| 03 | Pastas de áudio | [x] | `tests/pastas-audio.spec.ts` | cria pasta + faixas + label |
| 04 | Pasta por horário | [~] | `tests/pastas-audio.spec.ts` | folder-schedule persiste janela; elegibilidade no player = `fixme` |
| 05 | Data início/fim pastas | [~] | `tests/pastas-audio.spec.ts` | período persiste; elegibilidade no player = `fixme` |
| 06 | Sequencial/aleatório | [x] | `tests/radio-playlists.spec.ts`, `scheduler-fila.spec.ts` | flag round-trip; ordem em si = client-side (nota) |
| 07 | Spot a cada X min | [x] | `tests/spots.spec.ts` | interval + policy refletidos na fila |
| 08 | Spot não toca (positivo) | [x] | `tests/spots.spec.ts` | elegível + aparece no debug |
| 09 | Spot substituindo playlist | [x] | `tests/spots.spec.ts`, `scheduler-fila.spec.ts` | playlist coexiste com spot |
| 10 | /radio/playlists reconhece pasta | [x] | `tests/radio-playlists.spec.ts` | folder-schedule vincula folder_id |
| 11 | Seleção múltipla de áudios | [x] | `tests/radio-playlists.spec.ts` | track_ids em massa persiste |
| 13 | Mídias individuais | [x] | `tests/campanhas.spec.ts` | mídia avulsa usada em campanha |
| 14 | Reordenar mídias | [x] | `tests/campanhas.spec.ts` | items + /items/reorder (guarded) |
| 15 | Conteúdo não passa + debug | [x] | `tests/player.spec.ts`, `debug.spec.ts` | playlist + debug-playback |
| 16 | Duração automática | [~] | `tests/campanhas.spec.ts` | valida duration>0; `fixme` se assíncrono |
| 17 | Período na mídia | [~] | `tests/campanhas.spec.ts` | aceita starts/ends; `fixme` se período no item |
| 18 | Substituir mídia | [x] | `tests/campanhas.spec.ts` | replace-file mantém id e vínculo |
| 19 | Comandos desligar/reiniciar | [x] | `tests/dispositivos-comandos.spec.ts` | command + pending + histórico |
| 20 | Invalidar pareamento | [x] | `tests/dispositivos-comandos.spec.ts` | revoke-token → token antigo 403 |
| 21 | Não reiniciar player | [~] | `tests/dispositivos-comandos.spec.ts` | base server-side; no-reload real = `fixme` |
| 26 | Mistura áudio/rádio (backend) | [x] | `tests/radio-playlists.spec.ts` | audio_policy persiste |
| 27 | Nome da música OSD | [ ] | `tests/player.spec.ts` | `fixme` — overlay é client-side do Player |
| 31 | Versionamento de programação | [x] | `tests/scheduler-fila.spec.ts`, `player.spec.ts` | schedule_version incrementa |
| 32 | WebSocket/polling | [~] | `tests/player.spec.ts`, `scheduler-fila.spec.ts` | WS inexistente (doc); SSE testado; polling fallback = `fixme` |
| 33 | Cache controlado | [x] | `tests/player.spec.ts` | sem stale após mutação |
| 34 | Painel debug por dispositivo | [x] | `tests/debug.spec.ts` | debug-spots + debug-playback |
| 35 | Logs padronizados | [ ] | `tests/debug.spec.ts` | `fixme` — não observável por HTTP (usar pytest+caplog) |
| 36 | Windows Electron + min/max | [~] | `tests/electron-windows.spec.ts` | comando show_desktop via API; janela real = `fixme` (Playwright-Electron) |

## CORE — Scheduler/Fila (`tests/scheduler-fila.spec.ts`)
- [x] fila inicial coerente (playlist + spots)
- [x] spot entra/não entra conforme janela de horário
- [x] spot NÃO substitui playlist (coexistência)
- [x] flag sequencial vs aleatório refletida
- [x] mutação device-scoped incrementa schedule_version
- [x] /player/schedule reflete novo estado (sem stale)
- [x] debug-spots explica elegibilidade
- [x] SSE entrega push após mutação
- [ ] ordem aleatória sem repetição indevida → client-side (ver `audio_manager.test.js`)
- [ ] player atualiza sem reload completo → client-side (ver `player_sse.test.js`)
