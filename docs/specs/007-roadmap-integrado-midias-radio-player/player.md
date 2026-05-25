# SPEC 007 — Player

## Estado atual

- `Player.jsx` sincroniza campanha, playlist visual, radio, comandos, heartbeat e SSE.
- `MediaRenderer.jsx` toca midia visual e recebe `videoMuted`.
- `AudioPlayer.jsx` toca radio persistente com fade e `onTrackChange`.
- `useAudioConflictResolver.js` decide radio vs audio da midia.
- `PlayerOSD.jsx` mostra nome da musica atual.
- `commands.js` executa comandos e retorna `platform_unsupported` quando nao ha bridge.
- `repair.js` limpa pareamento e volta para tela de pareamento.

## Lacunas

- Nao existe audio manager central para spots.
- Shuffle precisa estrategia anti-repeticao.
- Radio por pasta/horario ainda nao existe no payload.
- Spots ainda nao existem.
- Status de cache por midia/dispositivo ainda nao existe.
- Shutdown depende de bridge nativa real por plataforma.

## Audio manager alvo

Criar uma camada com API:

```js
audioManager.setRadioQueue(queue)
audioManager.setMediaContext(media, policy)
audioManager.scheduleSpot(spot)
audioManager.tick(now)
audioManager.getState()
```

Estados:

- `idle`
- `radio_playing`
- `media_audio_playing`
- `spot_playing`
- `paused_for_policy`

Regras iniciais:

- spot pausa radio;
- video com audio em `auto` pausa radio;
- `mix` e a unica politica que permite dois audios;
- ao fim de spot, radio retoma de forma previsivel;
- se nao houver faixa valida, audio fica silencioso.

## Pareamento

Manter:

- `X-Device-Token-Version`;
- `forceRepair` em 401/403;
- SSE `pairing:revoked`;
- limpeza de localStorage/IndexedDB.

## Comandos

Manter:

- polling + SSE `command:new`;
- received/started/ack;
- pre-ACK para destrutivos.

Ampliar:

- logs locais por comando;
- resultado nativo quando Electron/APK retornarem detalhes;
- mensagem visual quando `platform_unsupported=true`.
