/**
 * factories.ts — builders de dados de alto nível sobre o Api client.
 * Tudo cria dado REAL no backend (sem mock). Nomes usam TEST_PREFIX p/ limpeza.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Api } from "./api.js";
import { genWav } from "./media-gen.js";
import { ENV, uniqueName } from "./env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MEDIA_DIR = path.resolve(__dirname, "../fixtures/media");

/** Sobe N faixas de áudio (WAV de silêncio) e devolve os objetos criados. */
export async function uploadAudioTracks(api: Api, n: number, opts: { seconds?: number } = {}): Promise<any[]> {
  const tracks: any[] = [];
  for (let i = 0; i < n; i++) {
    const wav = genWav(opts.seconds ?? 2);
    const t = await api.uploadTrack(wav, { name: uniqueName(`faixa-${i + 1}`) });
    tracks.push(t);
  }
  return tracks;
}

/** Cria categoria de áudio. */
export async function createCategory(api: Api, label = "cat"): Promise<any> {
  return api.createCategory({ name: uniqueName(label) });
}

/** Cria pasta de áudio e adiciona faixas. */
export async function createFolderWithTracks(api: Api, trackIds: string[], extra: Record<string, any> = {}): Promise<any> {
  const folder = await api.createFolder({ name: uniqueName("pasta"), ...extra });
  if (trackIds.length) await api.addTracksToFolder(folder.id, trackIds);
  return folder;
}

/** Cria playlist sonora com faixas (e flags de modo). */
export async function createPlaylist(
  api: Api,
  trackIds: string[],
  opts: { shuffle?: boolean; loop?: boolean; extra?: Record<string, any> } = {},
): Promise<any> {
  return api.createPlaylist({
    name: uniqueName("playlist"),
    track_ids: trackIds,
    shuffle_enabled: opts.shuffle ?? false,
    loop_enabled: opts.loop ?? true,
    status: "active",
    ...(opts.extra || {}),
  });
}

/** Cria spot (precisa de uma faixa de áudio como base). */
export async function createSpot(api: Api, trackId: string, opts: Record<string, any> = {}): Promise<any> {
  return api.createSpot({
    name: uniqueName("spot"),
    track_id: trackId,
    status: "active",
    insertion_policy: opts.insertion_policy ?? "wait_silence",
    ...opts,
  });
}

/** Sobe mídia de áudio (válida) para uso em campanha. */
export async function uploadAudioMedia(api: Api, opts: { seconds?: number } = {}): Promise<any> {
  const wav = genWav(opts.seconds ?? 3);
  return api.createMediaUpload(wav, { name: uniqueName("midia-audio"), media_type: "audio" });
}

/**
 * Retorna um asset de VÍDEO real se existir em fixtures/media/sample.mp4.
 * Vídeo válido não pode ser gerado em memória, então testes que exigem vídeo
 * devem checar `hasVideoFixture()` e pular com motivo quando ausente.
 */
export function hasVideoFixture(): boolean {
  return fs.existsSync(path.join(MEDIA_DIR, "sample.mp4"));
}

export function videoFixture(): { name: string; mimeType: string; buffer: Buffer } {
  const p = path.join(MEDIA_DIR, "sample.mp4");
  return { name: "sample.mp4", mimeType: "video/mp4", buffer: fs.readFileSync(p) };
}

/** Cria campanha vinculada a um device e (opcional) publica. */
export async function createCampaign(
  api: Api,
  opts: { deviceIds?: string[]; mediaIds?: string[]; audioPlaylistId?: string; publish?: boolean; extra?: Record<string, any> } = {},
): Promise<any> {
  const campaign = await api.createCampaign({
    name: uniqueName("campanha"),
    status: "active",
    priority: 5,
    device_ids: opts.deviceIds || [],
    media_ids: opts.mediaIds || [],
    audio_playlist_id: opts.audioPlaylistId,
    schedule_all_day: true,
    ...(opts.extra || {}),
  });
  if (opts.publish && opts.deviceIds?.length) {
    await api.publishCampaign(campaign.id, opts.deviceIds);
  }
  return campaign;
}

/** Garante que TENANT_ID esteja presente quando o teste precisar dele. */
export function requireTenant(): string {
  if (!ENV.TENANT_ID) {
    throw new Error("TENANT_ID não configurado no .env — necessário para este teste.");
  }
  return ENV.TENANT_ID;
}
