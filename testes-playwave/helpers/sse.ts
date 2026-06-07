/**
 * sse.ts — cliente SSE mínimo para validar push em tempo real do player.
 *
 * O backend NÃO usa WebSocket. Tempo real é Server-Sent Events:
 *   GET /devices/{id}/playlist/updates?token=<device_token>   (text/event-stream)
 * Eventos emitidos: snapshot, playlist_invalidated, command:new, pairing:revoked.
 *
 * Usa fetch streaming (Node 18+) para coletar eventos por um período.
 */
import { ENV } from "./env.js";

export interface SseEvent {
  event: string;
  data: string;
  at: number;
}

/**
 * Abre o stream e coleta eventos até `opts.collectMs` ou até `opts.until` casar.
 * Retorna todos os eventos vistos. Fecha o stream ao final.
 */
export async function collectSse(
  deviceId: string,
  deviceToken: string,
  opts: { collectMs?: number; until?: (e: SseEvent) => boolean; baseURL?: string } = {},
): Promise<SseEvent[]> {
  const baseURL = opts.baseURL || ENV.API_URL;
  const url = `${baseURL}/devices/${deviceId}/playlist/updates?token=${encodeURIComponent(deviceToken)}`;
  const collectMs = opts.collectMs ?? 5000;

  const controller = new AbortController();
  const events: SseEvent[] = [];
  const timer = setTimeout(() => controller.abort(), collectMs);

  try {
    const res = await fetch(url, {
      headers: { Accept: "text/event-stream" },
      signal: controller.signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`SSE connect falhou: ${res.status} ${res.statusText}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let curEvent = "message";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      let idx: number;
      while ((idx = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, idx).replace(/\r$/, "");
        buf = buf.slice(idx + 1);

        if (line.startsWith("event:")) {
          curEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          const ev: SseEvent = { event: curEvent, data: line.slice(5).trim(), at: Date.now() };
          events.push(ev);
          if (opts.until && opts.until(ev)) {
            controller.abort();
            return events;
          }
        } else if (line === "") {
          curEvent = "message"; // fim de um bloco de evento
        }
      }
    }
  } catch (err: any) {
    if (err?.name !== "AbortError") throw err;
  } finally {
    clearTimeout(timer);
  }

  return events;
}
