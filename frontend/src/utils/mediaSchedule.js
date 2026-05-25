/**
 * mediaSchedule.js — Utilitário de verificação de período de mídia
 * Extraído de Player.jsx (SPEC 001)
 */

export function isMediaCurrentlyPlayable(media, now = Date.now()) {
  if (!media) return false;
  if (media.status && media.status !== "available") return false;
  if (media.is_active === false) return false;

  const startsAt = media.starts_at ? Date.parse(media.starts_at) : null;
  if (Number.isFinite(startsAt) && startsAt > now) return false;

  const endsAt = media.ends_at ? Date.parse(media.ends_at) : null;
  if (Number.isFinite(endsAt) && endsAt < now) return false;

  return true;
}
