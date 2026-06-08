/**
 * mediaSchedule.js — Utilitário de verificação de período de mídia
 * Extraído de Player.jsx (SPEC 001)
 */

import { parseBackendDateTime } from "@/player-core/scheduleTime.js";

export function isMediaCurrentlyPlayable(media, now = Date.now()) {
  if (!media) return false;
  if (media.status && media.status !== "available") return false;
  if (media.is_active === false) return false;

  const nowMs = now instanceof Date ? now.getTime() : now;

  const startsAt = parseBackendDateTime(media.starts_at);
  if (startsAt && startsAt.getTime() > nowMs) return false;

  const endsAt = parseBackendDateTime(media.ends_at);
  if (endsAt && endsAt.getTime() < nowMs) return false;

  return true;
}
