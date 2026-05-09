const YOUTUBE_RE = /(?:youtube\.com\/watch\?.*v=|youtu\.be\/|youtube\.com\/embed\/)([^&?/\s]+)/;
const VIMEO_RE   = /vimeo\.com\/(\d+)/;

const IMAGE_EXTS = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]);
const VIDEO_EXTS = new Set([".mp4", ".webm", ".mov", ".mkv", ".avi"]);
const AUDIO_EXTS = new Set([".mp3", ".wav", ".ogg", ".m4a"]);

const API_BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

function extOf(url) {
  try {
    const path = new URL(url).pathname;
    return path.slice(path.lastIndexOf(".")).toLowerCase();
  } catch {
    const lower = url.toLowerCase().split("?")[0];
    return lower.slice(lower.lastIndexOf("."));
  }
}

/**
 * Converts a relative path (e.g. "/uploads/media/file.jpg") to an absolute URL
 * by prepending the API base URL. Absolute URLs are returned unchanged.
 */
export function assetUrl(path) {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) {
    return path;
  }
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

export function detectUrlMediaType(url) {
  if (!url) return "external_url";
  if (YOUTUBE_RE.test(url)) return "youtube";
  if (VIMEO_RE.test(url))   return "vimeo";
  const ext = extOf(url);
  if (IMAGE_EXTS.has(ext)) return "image";
  if (VIDEO_EXTS.has(ext)) return "video";
  if (AUDIO_EXTS.has(ext)) return "audio";
  return "external_url";
}

export function getYouTubeEmbedUrl(url) {
  const m = YOUTUBE_RE.exec(url);
  if (!m) return null;
  return `https://www.youtube.com/embed/${m[1]}?autoplay=1&rel=0`;
}

export function getVimeoEmbedUrl(url) {
  const m = VIMEO_RE.exec(url);
  if (!m) return null;
  return `https://player.vimeo.com/video/${m[1]}?autoplay=1`;
}

/**
 * Given a media object, returns the best src URL to use in an img/video/iframe.
 * - YouTube/Vimeo: returns the embed URL
 * - Local uploads (/uploads/...): prepends VITE_API_URL so the request goes to FastAPI
 * - Absolute URLs: returned as-is
 */
export function resolveMediaUrl(media) {
  if (!media?.file_url) return null;
  const url = media.file_url;
  const type = detectUrlMediaType(url);
  if (type === "youtube") return getYouTubeEmbedUrl(url);
  if (type === "vimeo")   return getVimeoEmbedUrl(url);
  return assetUrl(url);
}

/**
 * Returns the effective media type, taking youtube/vimeo into account even
 * when the stored `type` field is "external_url".
 */
export function resolveMediaType(media) {
  if (!media) return null;
  if (media.type === "external_url" || media.type === "youtube" || media.type === "vimeo") {
    const detected = detectUrlMediaType(media.file_url || "");
    return detected;
  }
  return media.type;
}
