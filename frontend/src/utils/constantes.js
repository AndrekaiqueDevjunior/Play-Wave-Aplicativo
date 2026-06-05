/**
 * utils/constantes.js
 * Constantes de domínio usadas em toda a aplicação — PT-BR
 */

// ── Dispositivos ──────────────────────────────────────────────────────────────

export const TIPOS_DISPOSITIVO = [
  { value: "tv", label: "TV" },
  { value: "tablet", label: "Tablet" },
  { value: "totem", label: "Totem" },
  { value: "smartphone", label: "Celular" },
  { value: "panel", label: "Painel" },
  { value: "other", label: "Outro" },
];

export const SISTEMAS_OPERACIONAIS = [
  "Web Player",
  "Android TV",
  "Windows",
  "iOS",
  "Linux",
];

export const STATUS_DISPOSITIVO = {
  online: { label: "Online", cor: "emerald" },
  offline: { label: "Offline", cor: "red" },
  syncing: { label: "Sincronizando", cor: "amber" },
  error: { label: "Erro", cor: "red" },
};

// ── Mídias ────────────────────────────────────────────────────────────────────

export const TIPOS_MIDIA = {
  image: { label: "Imagem", extensoes: ["jpg", "jpeg", "png", "gif", "webp"] },
  video: { label: "Vídeo", extensoes: ["mp4", "webm", "mov"] },
  audio: { label: "Áudio", extensoes: ["mp3", "wav", "ogg"] },
  external_url: { label: "URL Externa", extensoes: [] },
};

// ── Campanhas ─────────────────────────────────────────────────────────────────

export const STATUS_CAMPANHA = {
  draft: { label: "Rascunho", cor: "slate" },
  scheduled: { label: "Agendada", cor: "blue" },
  active: { label: "Ativa", cor: "emerald" },
  paused: { label: "Pausada", cor: "amber" },
  ended: { label: "Encerrada", cor: "slate" },
};

export const PRIORIDADES_CAMPANHA = [
  { value: 1, label: "Baixa" },
  { value: 2, label: "Média-Baixa" },
  { value: 3, label: "Média" },
  { value: 4, label: "Média-Alta" },
  { value: 5, label: "Alta" },
];

export const DIAS_SEMANA = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

// ── Rádio Indoor ──────────────────────────────────────────────────────────────

export const CATEGORIAS_AUDIO = {
  music: { label: "Música" },
  jingle: { label: "Jingle" },
  announcement: { label: "Anúncio" },
  ambient: { label: "Ambiente" },
  other: { label: "Outro" },
};

// ── Player ────────────────────────────────────────────────────────────────────

export const HEARTBEAT_INTERVALO_MS = 30_000;
export const POLL_PAREAMENTO_MS = 3_000;
export const PLAYER_VERSION = "3.1.0";
