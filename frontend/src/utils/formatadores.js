/**
 * utils/formatadores.js
 * Funções de formatação de dados para exibição na UI — PT-BR
 */

/** Formata bytes em KB ou MB legível */
export function formatarTamanho(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Formata segundos em mm:ss */
export function formatarDuracao(segundos) {
  if (!segundos) return "—";
  const m = Math.floor(segundos / 60);
  const s = Math.floor(segundos % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Formata data ISO em dd/mm/aaaa */
export function formatarData(isoString) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleDateString("pt-BR");
}

/** Formata data ISO em dd/mm/aaaa HH:MM */
export function formatarDataHora(isoString) {
  if (!isoString) return "—";
  return new Date(isoString).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Formata volume float (0.0–1.0) em porcentagem */
export function formatarVolume(volume) {
  return `${Math.round((volume ?? 0.7) * 100)}%`;
}

/** Trunca texto longo com reticências */
export function truncar(texto, limite = 50) {
  if (!texto) return "";
  return texto.length > limite ? texto.slice(0, limite) + "…" : texto;
}
