/**
 * api.ts — Cliente de API aterrado nos endpoints REAIS do backend PlayWave.
 *
 * Mapa de rotas (auditado em backend/api/v1):
 *   Auth:        POST /api/auth/login   GET /api/auth/me
 *   Devices:     /devices ...           POST /devices/{id}/command
 *                GET /devices/{id}/debug-spots | /debug-playback
 *                GET /devices/{id}/playlist            (X-Device-Token)
 *   Pareamento:  POST /devices/pair-request | GET /devices/by-code/{code}/status
 *                POST /devices/{id}/pair-confirm
 *   Player:      GET /api/v1/player/schedule?device_id=&device_token=
 *   SSE:         GET /devices/{id}/playlist/updates?token=   (text/event-stream)
 *   Áudio:       /audio/tracks (+/upload, /upload-multiple), /audio/categories,
 *                /audio/folders (+/{id}/tracks, /tracks/reorder),
 *                /audio/playlists (+/{id}/folder-schedules),
 *                /audio/spots (+/schedules, /playlists/{id}/spot-schedules)
 *   Mídia:       /media (+/upload, /{id}/replace-file, /{id}/usage, /{id}/versions)
 *   Campanhas:   /campaigns (+/{id}/publish, /{id}/items, /items/reorder)
 *
 * NÃO inventa endpoints. Se algo não existe, o teste correspondente marca TODO.
 */
import type { APIRequestContext, APIResponse } from "@playwright/test";
import { ENV } from "./env.js";

export interface PairedDevice {
  device_id: string;
  device_token: string;
  code: string;
  name: string;
}

export class Api {
  private token: string | null = null;

  constructor(private request: APIRequestContext, private baseURL = ENV.API_URL) {}

  // ─── Núcleo ────────────────────────────────────────────────────────────────
  private url(path: string): string {
    return `${this.baseURL}${path.startsWith("/") ? path : `/${path}`}`;
  }

  private authHeaders(extra: Record<string, string> = {}): Record<string, string> {
    return this.token ? { Authorization: `Bearer ${this.token}`, ...extra } : extra;
  }

  private async json<T = any>(res: APIResponse, ctx: string): Promise<T> {
    if (!res.ok()) {
      const body = await res.text().catch(() => "");
      throw new Error(`[API ${ctx}] ${res.status()} ${res.statusText()} :: ${body.slice(0, 500)}`);
    }
    const text = await res.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }

  /** Acesso bruto para asserts de status (ex: validar 403/422). */
  async raw(method: "get" | "post" | "put" | "patch" | "delete", path: string, opts: any = {}): Promise<APIResponse> {
    const headers = this.authHeaders(opts.headers || {});
    return this.request[method](this.url(path), { ...opts, headers });
  }

  // ─── Auth ──────────────────────────────────────────────────────────────────
  async login(email = ENV.ADMIN_EMAIL, password = ENV.ADMIN_PASSWORD): Promise<string> {
    const res = await this.request.post(this.url("/api/auth/login"), {
      data: { email, password },
    });
    const body = await this.json<{ access_token: string }>(res, "login");
    this.token = body.access_token;
    return this.token;
  }

  setToken(token: string) {
    this.token = token;
  }
  getToken() {
    return this.token;
  }

  async me(): Promise<any> {
    const res = await this.request.get(this.url("/api/auth/me"), { headers: this.authHeaders() });
    return this.json(res, "me");
  }

  // ─── Devices ───────────────────────────────────────────────────────────────
  async listDevices(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/devices${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listDevices");
  }

  async getDevice(id: string): Promise<any> {
    const res = await this.request.get(this.url(`/devices/${id}`), { headers: this.authHeaders() });
    return this.json(res, "getDevice");
  }

  async createDevice(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/devices"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createDevice");
  }

  async updateDevice(id: string, payload: Record<string, any>): Promise<any> {
    const res = await this.request.put(this.url(`/devices/${id}`), { headers: this.authHeaders(), data: payload });
    return this.json(res, "updateDevice");
  }

  async deleteDevice(id: string): Promise<void> {
    await this.request.delete(this.url(`/devices/${id}`), { headers: this.authHeaders() });
  }

  async deviceCommand(id: string, commandType: string, opts: { payload?: any; expiresInSeconds?: number } = {}): Promise<any> {
    const data: Record<string, any> = { command_type: commandType };
    if (opts.payload) data.payload = opts.payload;
    if (opts.expiresInSeconds != null) data.expires_in_seconds = opts.expiresInSeconds;
    const res = await this.request.post(this.url(`/devices/${id}/command`), { headers: this.authHeaders(), data });
    return this.json(res, "deviceCommand");
  }

  async listCommands(id: string, params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/devices/${id}/commands${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listCommands");
  }

  async pendingCommands(id: string, deviceToken: string): Promise<any[]> {
    const res = await this.request.get(this.url(`/devices/${id}/commands/pending`), {
      headers: { "X-Device-Token": deviceToken },
    });
    return this.json(res, "pendingCommands");
  }

  async revokeToken(id: string): Promise<any> {
    const res = await this.request.post(this.url(`/devices/${id}/revoke-token`), { headers: this.authHeaders() });
    return this.json(res, "revokeToken");
  }

  // ─── Pareamento (gera device + device_token reais) ──────────────────────────
  /**
   * Fluxo admin-first (validado): cria o device com `pairing_code` + status
   * waiting_pairing (tenant é herdado do admin no banco), depois
   * GET /devices/by-code/{code}/status emite o device_token.
   *
   * Notas de contrato real:
   *   - device_type aceita só tv|tablet|totem|smartphone|panel|other (web_player é OS).
   *   - DeviceResponse NÃO serializa tenant_id, mas o device fica com o tenant
   *     correto no banco (necessário para o resolver casar spots).
   */
  async pairDevice(opts: { name?: string; deviceType?: string; os?: string } = {}): Promise<PairedDevice> {
    const code = `TV-E2E${Math.floor(100000 + Math.random() * 899999)}`;
    const name = opts.name || `e2e-device-${code}`;

    const device = await this.createDevice({
      name,
      device_type: opts.deviceType || "tv",
      pairing_code: code,
      os: opts.os || "web_player",
    });
    const deviceId = device.id;

    const statusRes = await this.request.get(this.url(`/devices/by-code/${code}/status`));
    const status = await this.json<{ device_id?: string; device_token?: string }>(statusRes, "by-code-status");

    const device_token = status.device_token!;
    if (!device_token) {
      throw new Error(`pairDevice: backend não emitiu device_token para code=${code} (status=${JSON.stringify(status)})`);
    }
    return { device_id: deviceId, device_token, code, name };
  }

  // ─── Player: programação / fila resolvida ──────────────────────────────────
  /** GET /api/v1/player/schedule — fila resolvida server-side (spots + playlist + versão). */
  async playerSchedule(deviceId: string, deviceToken: string): Promise<any> {
    const res = await this.request.get(
      this.url(`/api/v1/player/schedule?device_id=${encodeURIComponent(deviceId)}&device_token=${encodeURIComponent(deviceToken)}`),
    );
    return this.json(res, "playerSchedule");
  }

  /** GET /devices/{id}/playlist — payload legado (X-Device-Token). */
  async devicePlaylist(deviceId: string, deviceToken: string): Promise<any> {
    const res = await this.request.get(this.url(`/devices/${deviceId}/playlist`), {
      headers: { "X-Device-Token": deviceToken },
    });
    return this.json(res, "devicePlaylist");
  }

  // ─── Debug (admin) ─────────────────────────────────────────────────────────
  async debugSpots(deviceId: string): Promise<any> {
    const res = await this.request.get(this.url(`/devices/${deviceId}/debug-spots`), { headers: this.authHeaders() });
    return this.json(res, "debugSpots");
  }

  async debugPlayback(deviceId: string): Promise<any> {
    const res = await this.request.get(this.url(`/devices/${deviceId}/debug-playback`), { headers: this.authHeaders() });
    return this.json(res, "debugPlayback");
  }

  // ─── Áudio: faixas ─────────────────────────────────────────────────────────
  async listTracks(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/tracks${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listTracks");
  }

  async uploadTrack(file: { name: string; mimeType: string; buffer: Buffer }, fields: Record<string, string> = {}): Promise<any> {
    const res = await this.request.post(this.url("/audio/tracks/upload"), {
      headers: this.authHeaders(),
      multipart: { file, name: fields.name || file.name, ...fields },
    });
    return this.json(res, "uploadTrack");
  }

  /**
   * Sobe N faixas de uma vez em POST /audio/tracks/upload-multiple.
   * O endpoint usa `files: List[UploadFile]` (mesma chave repetida). Playwright
   * não expressa isso no objeto `multipart`, então montamos o corpo
   * multipart/form-data manualmente e enviamos como Buffer.
   */
  async uploadTracksMultiple(
    files: { name: string; mimeType: string; buffer: Buffer }[],
    fields: Record<string, string> = {},
  ): Promise<any> {
    const { body, contentType } = encodeMultipart(
      files.map((f) => ({ field: "files", filename: f.name, mimeType: f.mimeType, buffer: f.buffer })),
      fields,
    );
    const res = await this.request.post(this.url("/audio/tracks/upload-multiple"), {
      headers: this.authHeaders({ "Content-Type": contentType }),
      data: body,
    });
    return this.json(res, "uploadTracksMultiple");
  }

  // ─── Áudio: categorias ─────────────────────────────────────────────────────
  async listCategories(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/categories${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listCategories");
  }

  async createCategory(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/audio/categories/"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createCategory");
  }

  // ─── Áudio: pastas ─────────────────────────────────────────────────────────
  async createFolder(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/audio/folders"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createFolder");
  }

  async listFolders(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/folders${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listFolders");
  }

  async addTracksToFolder(folderId: string, trackIds: string[]): Promise<any> {
    const res = await this.request.post(this.url(`/audio/folders/${folderId}/tracks`), {
      headers: this.authHeaders(),
      data: { tracks: trackIds.map((id) => ({ track_id: id })) },
    });
    return this.json(res, "addTracksToFolder");
  }

  async listFolderTracks(folderId: string): Promise<any[]> {
    const res = await this.request.get(this.url(`/audio/folders/${folderId}/tracks`), { headers: this.authHeaders() });
    return this.json(res, "listFolderTracks");
  }

  async reorderFolderTracks(folderId: string, items: { id: string; position: number }[]): Promise<any> {
    const res = await this.request.patch(this.url(`/audio/folders/${folderId}/tracks/reorder`), {
      headers: this.authHeaders(),
      data: { items },
    });
    return this.json(res, "reorderFolderTracks");
  }

  // ─── Áudio: playlists ──────────────────────────────────────────────────────
  async createPlaylist(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/audio/playlists"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createPlaylist");
  }

  async getPlaylist(id: string): Promise<any> {
    const res = await this.request.get(this.url(`/audio/playlists/${id}`), { headers: this.authHeaders() });
    return this.json(res, "getPlaylist");
  }

  async listPlaylists(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/playlists${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listPlaylists");
  }

  async createFolderSchedule(playlistId: string, payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url(`/audio/playlists/${playlistId}/folder-schedules`), {
      headers: this.authHeaders(),
      data: payload,
    });
    return this.json(res, "createFolderSchedule");
  }

  // ─── Áudio: spots ──────────────────────────────────────────────────────────
  async createSpot(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/audio/spots"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createSpot");
  }

  async listSpots(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/spots${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listSpots");
  }

  /** Cria schedule por escopo (playlist_id | campaign_id | device_id no corpo). */
  async createSpotSchedule(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/audio/spots/schedules"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createSpotSchedule");
  }

  async createSpotScheduleForPlaylist(playlistId: string, payload: Record<string, any>): Promise<any> {
    // O schema AudioSpotScheduleCreate valida "pelo menos um escopo" no CORPO,
    // antes de o endpoint injetar o playlist_id do path. Então enviamos
    // playlist_id também no body (contrato real do backend).
    const res = await this.request.post(this.url(`/audio/spots/playlists/${playlistId}/spot-schedules`), {
      headers: this.authHeaders(),
      data: { playlist_id: playlistId, ...payload },
    });
    return this.json(res, "createSpotScheduleForPlaylist");
  }

  async listSpotSchedules(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/audio/spots/schedules${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listSpotSchedules");
  }

  async updateSpotSchedule(scheduleId: string, payload: Record<string, any>): Promise<any> {
    const res = await this.request.put(this.url(`/audio/spots/schedules/${scheduleId}`), {
      headers: this.authHeaders(),
      data: payload,
    });
    return this.json(res, "updateSpotSchedule");
  }

  async deleteSpotSchedule(scheduleId: string): Promise<void> {
    await this.request.delete(this.url(`/audio/spots/schedules/${scheduleId}`), { headers: this.authHeaders() });
  }

  // ─── Mídia ─────────────────────────────────────────────────────────────────
  async createMediaUpload(file: { name: string; mimeType: string; buffer: Buffer }, fields: Record<string, string> = {}): Promise<any> {
    const res = await this.request.post(this.url("/media/upload"), {
      headers: this.authHeaders(),
      multipart: { file, name: fields.name || file.name, ...fields },
    });
    return this.json(res, "createMediaUpload");
  }

  async listMedia(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await this.request.get(this.url(`/media/${qs ? `?${qs}` : ""}`), { headers: this.authHeaders() });
    return this.json(res, "listMedia");
  }

  async replaceMediaFile(mediaId: string, file: { name: string; mimeType: string; buffer: Buffer }): Promise<any> {
    const res = await this.request.post(this.url(`/media/${mediaId}/replace-file`), {
      headers: this.authHeaders(),
      multipart: { file },
    });
    return this.json(res, "replaceMediaFile");
  }

  async mediaUsage(mediaId: string): Promise<any> {
    const res = await this.request.get(this.url(`/media/${mediaId}/usage`), { headers: this.authHeaders() });
    return this.json(res, "mediaUsage");
  }

  // ─── Campanhas ─────────────────────────────────────────────────────────────
  async createCampaign(payload: Record<string, any>): Promise<any> {
    const res = await this.request.post(this.url("/campaigns"), { headers: this.authHeaders(), data: payload });
    return this.json(res, "createCampaign");
  }

  async getCampaign(id: string): Promise<any> {
    const res = await this.request.get(this.url(`/campaigns/${id}`), { headers: this.authHeaders() });
    return this.json(res, "getCampaign");
  }

  async updateCampaign(id: string, payload: Record<string, any>): Promise<any> {
    const res = await this.request.put(this.url(`/campaigns/${id}`), { headers: this.authHeaders(), data: payload });
    return this.json(res, "updateCampaign");
  }

  async publishCampaign(id: string, deviceIds?: string[]): Promise<any> {
    const res = await this.request.post(this.url(`/campaigns/${id}/publish`), {
      headers: this.authHeaders(),
      data: deviceIds ? { device_ids: deviceIds } : {},
    });
    return this.json(res, "publishCampaign");
  }

  async deleteCampaign(id: string): Promise<void> {
    await this.request.delete(this.url(`/campaigns/${id}`), { headers: this.authHeaders() });
  }

  // ─── Esperas (fila / versão) ───────────────────────────────────────────────
  /** Faz polling em GET /devices/{id} até `predicate(device)` ou timeout. */
  async waitForDevice(
    id: string,
    predicate: (device: any) => boolean,
    timeout = ENV.QUEUE_WAIT_TIMEOUT,
    intervalMs = 500,
  ): Promise<any> {
    const start = Date.now();
    let last: any = null;
    while (Date.now() - start < timeout) {
      last = await this.getDevice(id);
      if (predicate(last)) return last;
      await sleep(intervalMs);
    }
    throw new Error(`waitForDevice: timeout após ${timeout}ms (device=${id}). Último: schedule_version=${last?.schedule_version}`);
  }

  /** Espera schedule_version do device passar de um valor de referência. */
  async waitForScheduleVersionAbove(id: string, baseline: number, timeout?: number): Promise<any> {
    return this.waitForDevice(id, (d) => Number(d.schedule_version) > baseline, timeout);
  }

  /** Espera um item entrar na fila resolvida do player (por predicado). */
  async waitForQueue(
    deviceId: string,
    deviceToken: string,
    predicate: (schedule: any) => boolean,
    timeout = ENV.QUEUE_WAIT_TIMEOUT,
    intervalMs = 700,
  ): Promise<any> {
    const start = Date.now();
    let last: any = null;
    while (Date.now() - start < timeout) {
      last = await this.playerSchedule(deviceId, deviceToken);
      if (predicate(last)) return last;
      await sleep(intervalMs);
    }
    throw new Error(`waitForQueue: timeout após ${timeout}ms (device=${deviceId}).`);
  }
}

export function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

// ─── Encoder multipart/form-data (suporta N arquivos na mesma chave) ──────────
interface MultipartFile {
  field: string;
  filename: string;
  mimeType: string;
  buffer: Buffer;
}

function encodeMultipart(filesParts: MultipartFile[], fields: Record<string, string>): { body: Buffer; contentType: string } {
  const boundary = `----pwE2E${Math.random().toString(36).slice(2)}`;
  const chunks: Buffer[] = [];
  const CRLF = "\r\n";

  for (const [name, value] of Object.entries(fields)) {
    chunks.push(Buffer.from(`--${boundary}${CRLF}Content-Disposition: form-data; name="${name}"${CRLF}${CRLF}${value}${CRLF}`));
  }
  for (const f of filesParts) {
    chunks.push(
      Buffer.from(
        `--${boundary}${CRLF}Content-Disposition: form-data; name="${f.field}"; filename="${f.filename}"${CRLF}Content-Type: ${f.mimeType}${CRLF}${CRLF}`,
      ),
    );
    chunks.push(f.buffer);
    chunks.push(Buffer.from(CRLF));
  }
  chunks.push(Buffer.from(`--${boundary}--${CRLF}`));

  return { body: Buffer.concat(chunks), contentType: `multipart/form-data; boundary=${boundary}` };
}
