import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  isApiConfigured,
  pairRequest,
  getPairStatus,
  getDevicePlaylist,
  sendHeartbeat,
} from "@/lib/api";
import { getBaseUrl } from "@/api/http";
import {
  registrarPlayback,
  buscarComandosPendentes,
  marcarComandoRecebido,
  marcarComandoIniciado,
  ackComando,
  abrirStreamPlaylistUpdates,
} from "@/api/dispositivos";
import PairingScreen from "@/components/player/PairingScreen";
import LoadingScreen from "@/components/player/LoadingScreen";
import ErrorScreen from "@/components/player/ErrorScreen";
import MediaRenderer from "@/components/player/MediaRenderer";
import PlayerOSD from "@/components/player/PlayerOSD";
import { assetUrl } from "@/utils/mediaUtils";
import { isMediaCurrentlyPlayable } from "@/utils/mediaSchedule";
import { PairingStorage, PlaylistCache } from "@/player-core/storage";
import { executeCommand, DESTRUCTIVE_COMMANDS } from "@/player-core/commands";
import { onForceRepair } from "@/player-core/repair";
import Platform, { acquireWakeLock, releaseWakeLock } from "@/player-core/platform";
import { startWatchdog, stopWatchdog, notifyHeartbeatOk, useOnlineStatus } from "@/player-core/network";
import { useAudioConflictResolver } from "@/hooks/useAudioConflictResolver";
import { createAudioManager, AUDIO_STATE, AUDIO_MODE } from "@/lib/audioManager";
import { logTrackStarted, logTrackEnded } from "@/lib/playbackEventLogger";

const HEARTBEAT_INTERVAL = 30_000;
const POLL_PAIRING_INTERVAL = 3_000;
const POLL_PLAYLIST_INTERVAL = 30_000;
const POLL_COMMANDS_INTERVAL = 10_000;
const PLAYER_VERSION = "3.1.0";

function generateCode() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  return (
    "TV-" +
    Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("")
  );
}

function getDebugMode() {
  if (typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  return params.get("debug") === "true" || localStorage.getItem("pw_player_debug") === "true";
}

function mediaVersionToken(media) {
  return [media?.file_version, media?.file_hash].filter(Boolean).join("-");
}

function withMediaVersion(url, media) {
  if (!url) return url;
  const token = mediaVersionToken(media);
  if (!token) return url;
  try {
    const parsed = new URL(url, window.location.origin);
    parsed.searchParams.set("v", String(media.file_version || 1));
    if (media.file_hash) parsed.searchParams.set("h", String(media.file_hash).slice(0, 12));
    return parsed.toString();
  } catch {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}v=${encodeURIComponent(token)}`;
  }
}


function normalizePlaylistMedia(media) {
  const absoluteUrl = assetUrl(media.file_url);
  const absoluteThumb = media.thumbnail_url ? assetUrl(media.thumbnail_url) : media.thumbnail_url;
  return {
    ...media,
    id: media.id || media.media_id,
    file_url: withMediaVersion(absoluteUrl, media),
    thumbnail_url: withMediaVersion(absoluteThumb, media),
    cache_key: `${media.id || media.media_id}:${media.file_version || 1}:${media.file_hash || ""}`,
  };
}

function PlayerDebugOverlay({ data }) {
  if (!data?.enabled) return null;
  const rows = [
    ["device", data.deviceId || "-"],
    ["pairing", data.pairingCode || "-"],
    ["platform", `${data.platform} / capacitor=${data.isCapacitor ? "yes" : "no"}`],
    ["phase", data.phase],
    ["online", String(data.isOnline)],
    ["campaign", data.campaignId || "-"],
    ["index", `${data.currentIndex + 1}/${data.totalItems}`],
    ["loops", data.schedule?.loopCount
      ? `${data.loopsCompleted}/${data.schedule.loopCount}`
      : `${data.loopsCompleted}/∞`],
    ["stopAt", data.schedule?.endDate || data.schedule?.scheduleEndTime || "-"],
    ["media", data.media ? `${data.media.type} - ${data.media.name}` : "-"],
    ["url", data.media?.file_url || "-"],
    ["next", data.nextMedia ? `${data.nextMedia.type} - ${data.nextMedia.name}` : "-"],
    ["lastSync", data.lastSync || "-"],
    ["videoEvent", data.video?.event || "-"],
    ["ready/network", `${data.video?.readyState ?? "-"} / ${data.video?.networkState ?? "-"}`],
    ["play", data.video?.paused === false ? "playing" : "not playing"],
    ["videoError", data.video?.error?.name || data.lastError?.event || "-"],
  ];

  return (
    <div className="fixed left-2 top-2 z-50 max-w-[92vw] w-[460px] rounded bg-black/80 p-3 text-[11px] leading-snug text-lime-100 font-mono pointer-events-none">
      <div className="mb-1 text-white font-semibold">PLAYWAVE DEBUG</div>
      {rows.map(([key, value]) => (
        <div key={key} className="grid grid-cols-[90px_1fr] gap-2 border-t border-white/10 py-0.5">
          <span className="text-white/50">{key}</span>
          <span className="truncate">{String(value)}</span>
        </div>
      ))}
    </div>
  );
}

export default function Player() {
  const saved = PairingStorage.load();
  const isOnline = useOnlineStatus();
  const debugMode = useMemo(getDebugMode, []);

  // Generate or reuse pairing code (setter usado em renovação por expiração ou forceRepair)
  const [pairingCode, setPairingCode] = useState(() => saved.code || generateCode());

  // If we already have device credentials, start in "loading" to skip pairing
  const [phase, setPhase] = useState(
    () => (saved.id && saved.token ? "loading" : "waiting"),
  );

  const [deviceId,    setDeviceId]    = useState(saved.id);
  const [deviceToken, setDeviceToken] = useState(saved.token);
  const [deviceName,  setDeviceName]  = useState("");
  const [playlist,    setPlaylist]    = useState([]);
  const [audioPlaylist, setAudioPlaylist] = useState(null);
  const [osdConfig, setOsdConfig] = useState({
    show_current_audio: true,
    position: "top_right",
    duration_seconds: 8,
    opacity: 0.6,
    font_size: "medium",
  });
  const [currentAudioTrack, setCurrentAudioTrack] = useState(null);
  const [campaignId, setCampaignId] = useState(null);
  const [campaignConfigVersion, setCampaignConfigVersion] = useState(null);
  const [campaign, setCampaign] = useState(null);  // SPEC 005: objeto campanha completo
  const [videoMuted, setVideoMuted] = useState(true); // legado — mantido para compat SSE
  const [audioManagerCurrent, setAudioManagerCurrent] = useState(AUDIO_STATE.SILENT);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress,   setProgress]    = useState(0);
  const [viewsCount, setViewsCount]  = useState(0);
  // Critérios de parada da campanha — preenchidos pelo /playlist
  // schedule: { endDate?: ISO, scheduleEndTime?: "HH:MM", loopCount?: number }
  const [campaignSchedule, setCampaignSchedule] = useState(null);
  const [loopsCompleted, setLoopsCompleted] = useState(0);
  const [apiStatus,  setApiStatus]   = useState(
    isApiConfigured() ? "connecting" : "no_api",
  );
  const [videoDebug, setVideoDebug] = useState(null);
  const [lastError, setLastError] = useState(null);
  const [lastSync, setLastSync] = useState(null);
  // SPEC 004 — quando forceRepair dispara, mostramos um banner explicativo
  // na tela de pareamento.
  const [forceRepairReason, setForceRepairReason] = useState(null);

  const pollPairRef      = useRef(null);
  const pollPlaylistRef  = useRef(null);
  const pollCommandsRef  = useRef(null);
  const heartbeatRef     = useRef(null);
  const progressRef      = useRef(null);
  const startTimeRef     = useRef(null);
  const deviceTokenRef   = useRef(deviceToken);
  const sseRef           = useRef(null);
  const failedMediaIdsRef = useRef(new Set());
  const trackStartedAtRef = useRef(null);
  const audioManagerRef  = useRef(null);
  const deviceIdRef      = useRef(deviceId);
  const audioPlaylistIdRef = useRef(null);
  const prevAudioTrackRef = useRef(null);

  // Keep refs in sync so mount-time closures always see latest values
  useEffect(() => { deviceTokenRef.current = deviceToken; }, [deviceToken]);
  useEffect(() => { deviceIdRef.current = deviceId; }, [deviceId]);

  // ── 0. Inicialização da plataforma ────────────────────────────────────────
  useEffect(() => {
    const apiBase = getBaseUrl();
    console.log("[player] platform:", Platform.name, "online:", isOnline, "api:", apiBase || "(relative)");
    // Sanity-check: APK/Capacitor com base em localhost = APK foi compilado com .env de dev.
    // No celular, localhost aponta para o próprio aparelho — API e mídia nunca carregam.
    if (Platform.isCapacitor && /localhost|127\.0\.0\.1/.test(apiBase)) {
      console.error(
        "[player] FATAL_CONFIG: VITE_API_URL aponta para localhost dentro de APK Capacitor.",
        "Recompile com .env.production apontando para o domínio público (npm run build:apk).",
        { apiBase },
      );
    }
    acquireWakeLock();
    startWatchdog(120_000, () => {
      // SPEC 004 — durante pairing/waiting o player nao tem credenciais válidas;
      // forçar reload aqui só vai entrar em loop. Skip.
      if (phase === "waiting" || phase === "pairing") {
        console.log("[player] watchdog skip — em fase de pareamento");
        return;
      }
      console.warn("[player] watchdog triggered — forcing reload of playlist");
      setPhase("loading");
    });

    // SPEC 004 — registra callback chamado por forceRepair() (repair.js).
    onForceRepair((reason) => {
      console.warn("[player] forceRepair callback:", reason);
      setForceRepairReason(reason);
      setDeviceId(null);
      setDeviceToken(null);
      setPlaylist([]);
      setAudioPlaylist(null);
      setCampaignId(null);
      setCurrentIndex(0);
      setProgress(0);

      // SPEC 004 — quando o admin regenera o código, o pairing_code do
      // dispositivo muda no backend. O código salvo no estado é stale e
      // nunca vai encontrar o dispositivo ao polling. Gera código novo para
      // que o admin pareie usando o código visível na TV.
      if (reason === "code_regenerated") {
        const newCode = generateCode();
        PairingStorage.save({ code: newCode });
        setPairingCode(newCode);
      }

      setPhase("waiting");
    });

    return () => {
      releaseWakeLock();
      stopWatchdog();
    };
  }, []);

  // ── 0b. Audio Manager — motor de áudio central ───────────────────────────
  useEffect(() => {
    const radio = document.createElement("audio");
    radio.preload = "auto";

    const spot = document.createElement("audio");
    spot.preload = "none";

    const mgr = createAudioManager({ fadeMs: 200 });
    mgr.initPlayers(radio, null, spot);

    const unsub = mgr.subscribe((newState) => {
      if ("currentTrack" in newState) {
        const newTrack = newState.currentTrack || null;
        const prevTrack = prevAudioTrackRef.current;

        // Log ended event for the previous track
        if (prevTrack && prevTrack !== newTrack) {
          const startedAt = trackStartedAtRef.current;
          const durationSecs = startedAt
            ? Math.round((Date.now() - new Date(startedAt).getTime()) / 1000)
            : null;
          logTrackEnded(deviceIdRef.current, prevTrack.id, durationSecs, audioPlaylistIdRef.current).catch(() => {});
        }

        if (newTrack) {
          const now = new Date().toISOString();
          trackStartedAtRef.current = now;
          logTrackStarted(deviceIdRef.current, newTrack.id, audioPlaylistIdRef.current, now).catch(() => {});
        } else {
          trackStartedAtRef.current = null;
        }

        prevAudioTrackRef.current = newTrack;
        setCurrentAudioTrack(newTrack);
      }
      if ("current" in newState) {
        setAudioManagerCurrent(newState.current);
      }
    });

    audioManagerRef.current = mgr;

    return () => {
      unsub();
      mgr.destroy();
      radio.pause(); radio.src = "";
      spot.pause(); spot.src = "";
    };
  }, []);

  // ── 1. Register pairing code ─────────────────────────────────────────────
  useEffect(() => {
    if (!isApiConfigured() || phase !== "waiting") return;
    pairRequest({ pairing_code: pairingCode, player_version: PLAYER_VERSION, os: "Web Player" })
      .then(() => setApiStatus("connected"))
      .catch(() => setApiStatus("error"));
  }, [pairingCode, phase]);

  // ── 2. Poll pairing status (waiting phase) ───────────────────────────────
  useEffect(() => {
    if (phase !== "waiting" || !isApiConfigured()) return;

    const poll = async () => {
      try {
        const res = await getPairStatus(pairingCode);
        console.log("[player] pairing poll:", res);
        if (res?.status === "paired" && res.device_id && res.device_token) {
          clearInterval(pollPairRef.current);
          // SPEC 004 — persiste tambem token_version e pairing_version para o
          // interceptor http enviar X-Device-Token-Version nas proximas requests.
          PairingStorage.save({
            code: pairingCode,
            id: res.device_id,
            token: res.device_token,
            tokenVersion: res.token_version,
            pairingVersion: res.pairing_version,
          });
          setDeviceId(res.device_id);
          setDeviceToken(res.device_token);
          setForceRepairReason(null);
          deviceTokenRef.current = res.device_token;
          setPhase("loading");
        } else if (res?.status === "expired") {
          // SPEC 004 — código expirou sem confirmação: gera um novo código.
          // O código anterior não tem mais entrada válida no backend.
          clearInterval(pollPairRef.current);
          console.warn("[player] pairing code expired — generating new code");
          const newCode = generateCode();
          PairingStorage.save({ code: newCode });
          setPairingCode(newCode);
          setForceRepairReason("PAIRING_CODE_EXPIRED");
        }
      } catch (err) {
        console.warn("[player] pairing poll error:", err);
      }
    };

    poll();
    pollPairRef.current = setInterval(poll, POLL_PAIRING_INTERVAL);
    return () => clearInterval(pollPairRef.current);
  }, [phase, pairingCode]);

  // ── 3. Load playlist ─────────────────────────────────────────────────────
  const loadPlaylist = useCallback(async (id, token) => {
    console.log("[player] loadPlaylist device_id=", id, "has_token=", !!token);
    try {
      const res = await getDevicePlaylist(id, token);
      console.log("[player] playlist response:", res);
      if (res?.device_name) setDeviceName(res.device_name);

      const medias = (res?.media || [])
        .filter((m) => isMediaCurrentlyPlayable(m))
        .map(normalizePlaylistMedia);
      setLastSync(new Date().toISOString());

      if (res?.campaign?.id) {
        setCampaignId(res.campaign.id);
        setCampaignConfigVersion(res.campaign.config_version || null);
        setCampaign(res.campaign);  // SPEC 005: guarda objeto completo
      } else {
        setCampaignId(null);
        setCampaignConfigVersion(null);
        setCampaign(null);
      }
      setVideoMuted(res?.campaign?.video_muted !== false);
      const ap = res?.audio_playlist || null;
      setAudioPlaylist(ap);
      audioPlaylistIdRef.current = ap?.id || null;
      setOsdConfig(res?.osd_config || {
        show_current_audio: true,
        position: "top_right",
        duration_seconds: 8,
        opacity: 0.6,
        font_size: "medium",
      });
      setCampaignSchedule(res?.campaign ? {
        endDate: res.campaign.end_date || null,
        scheduleEndTime: res.campaign.schedule_end_time || null,
        loopCount: res.campaign.loop_count ?? null,
      } : null);
      setLoopsCompleted(0);

      if (medias.length > 0) {
        failedMediaIdsRef.current.clear();
        setPlaylist(medias);
        setCurrentIndex(0);
        setProgress(0);
        setPhase("playing");
        PlaylistCache.set(id, { medias, timestamp: Date.now() }).catch(() => {});
        return true;
      }
      return false;
    } catch (err) {
      console.error("[player] loadPlaylist error:", err);
      throw err;
    }
  }, []);

  useEffect(() => {
    if (phase !== "loading" || !deviceId || !deviceToken) return;

    loadPlaylist(deviceId, deviceToken).then((hasMedeia) => {
      if (!hasMedeia) {
        console.log("[player] no media yet, entering no_campaign phase");
        setPhase("no_campaign");
      }
    }).catch(async (err) => {
      const msg = err?.message || "";
      const isAuthError = msg.includes("401") || msg.includes("403") || msg.includes("Token");
      if (isAuthError) {
        console.error("[player] auth error, clearing saved pairing:", msg);
        PairingStorage.clear();
        setDeviceId(null);
        setDeviceToken(null);
        setPhase("waiting");
      } else {
        console.error("[player] playlist load failed — trying cache, then no_campaign:", msg);
        const cached = await PlaylistCache.get(deviceId).catch(() => null);
        const cachedMedias = (cached?.medias || []).filter((m) => isMediaCurrentlyPlayable(m));
        if (cachedMedias.length > 0) {
          console.log("[player] using cached playlist (", cachedMedias.length, "items)");
          setPlaylist(cachedMedias);
          setCurrentIndex(0);
          setProgress(0);
          setPhase("playing");
        } else {
          setPhase("no_campaign");
        }
      }
    });
  }, [phase, deviceId, deviceToken, loadPlaylist]);

  // ── 4. Poll for campaign when device has no campaign yet ─────────────────
  useEffect(() => {
    if (phase !== "no_campaign" || !deviceId || !deviceToken) return;

    const poll = async () => {
      console.log("[player] no_campaign poll for new playlist...");
      try {
        const hasMidia = await loadPlaylist(deviceId, deviceToken);
        if (hasMidia) clearInterval(pollPlaylistRef.current);
      } catch {
        /* ignore */
      }
    };

    poll();
    pollPlaylistRef.current = setInterval(poll, POLL_PLAYLIST_INTERVAL);
    return () => clearInterval(pollPlaylistRef.current);
  }, [phase, deviceId, deviceToken, loadPlaylist]);

  const selectNextPlayableIndex = useCallback((fromIndex) => {
    if (playlist.length <= 1) return 0;
    for (let step = 1; step <= playlist.length; step += 1) {
      const nextIndex = (fromIndex + step) % playlist.length;
      const nextMedia = playlist[nextIndex];
      if (nextMedia && !failedMediaIdsRef.current.has(nextMedia.id)) {
        return nextIndex;
      }
    }
    failedMediaIdsRef.current.clear();
    return (fromIndex + 1) % playlist.length;
  }, [playlist]);

  const advanceMedia = useCallback((reason = "advance") => {
    if (!playlist.length) return;
    const currentMedia = playlist[currentIndex];
    // Para playback log: usa tempo real desde o startTime quando duration não
    // foi definida (vídeo/áudio com duração natural).
    const elapsedMs = startTimeRef.current
      ? Math.max(Date.now() - startTimeRef.current, 0)
      : 0;
    const duration = currentMedia?.duration && currentMedia.duration > 0
      ? currentMedia.duration * 1000
      : elapsedMs;
    const failed = String(reason).startsWith("failed");

    if (currentMedia && campaignId && deviceToken) {
      registrarPlayback(deviceId, deviceToken, {
        campaign_id: campaignId,
        media_id: currentMedia.id,
        started_at: new Date(Date.now() - duration).toISOString(),
        ended_at: new Date().toISOString(),
        duration_ms: duration,
        status: failed ? "failed" : "completed",
      }).catch(() => {});
    }

    setCurrentIndex((prev) => {
      const next = selectNextPlayableIndex(prev);
      // Detecta volta completa da playlist: chegou no fim e voltou para 0 (ou retornou ao primeiro válido).
      if (next <= prev) {
        setLoopsCompleted((n) => n + 1);
      }
      return next;
    });
    setViewsCount((prev) => prev + 1);
  }, [campaignId, currentIndex, deviceId, deviceToken, playlist, selectNextPlayableIndex]);

  const handleMediaError = useCallback((payload) => {
    const currentMedia = playlist[currentIndex];
    const errorPayload = {
      ...payload,
      currentIndex,
      media_id: currentMedia?.id || payload?.media?.id || null,
      timestamp: new Date().toISOString(),
    };
    console.error("[player] media failed, skipping:", errorPayload);
    setLastError(errorPayload);
    if (currentMedia?.id) failedMediaIdsRef.current.add(currentMedia.id);
    setTimeout(() => advanceMedia(`failed:${payload?.event || "media_error"}`), 500);
  }, [advanceMedia, currentIndex, playlist]);

  // ── 5a. Stop condition: end_date / schedule_end_time / loop_count ────────
  // Programa um setTimeout cravado para o instante de parada e força recarga.
  // O backend reavaliará e retornará vazio se a campanha tiver expirado.
  useEffect(() => {
    if (phase !== "playing" || !campaignSchedule) return;

    // 1) Parada por loop_count atingido → força reload imediato
    if (campaignSchedule.loopCount && loopsCompleted >= campaignSchedule.loopCount) {
      console.log("[player] loop_count atingido:", loopsCompleted, "/", campaignSchedule.loopCount);
      setPhase("loading");
      return;
    }

    // 2) Calcula o instante absoluto de parada (menor entre end_date e schedule_end_time hoje)
    const now = Date.now();
    const stopAtCandidates = [];

    if (campaignSchedule.endDate) {
      const endDateMs = Date.parse(campaignSchedule.endDate);
      if (Number.isFinite(endDateMs) && endDateMs > now) stopAtCandidates.push(endDateMs);
    }

    if (campaignSchedule.scheduleEndTime) {
      const match = /^(\d{1,2}):(\d{2})/.exec(campaignSchedule.scheduleEndTime);
      if (match) {
        const today = new Date();
        today.setHours(Number(match[1]), Number(match[2]), 0, 0);
        const stopToday = today.getTime();
        if (stopToday > now) stopAtCandidates.push(stopToday);
      }
    }

    if (stopAtCandidates.length === 0) return;

    const stopAt = Math.min(...stopAtCandidates);
    const delay = Math.min(stopAt - now, 2_147_483_000); // cap setTimeout 32-bit
    console.log("[player] stop scheduled for", new Date(stopAt).toISOString(), `(in ${Math.round(delay / 1000)}s)`);

    const timer = setTimeout(() => {
      console.log("[player] stop time reached — reloading playlist for re-evaluation");
      setPhase("loading");
    }, delay);

    return () => clearTimeout(timer);
  }, [phase, campaignSchedule, loopsCompleted]);

  // ── 5. Progress + media advance ──────────────────────────────────────────
  useEffect(() => {
    if (phase !== "playing" || playlist.length === 0) return;
    const media = playlist[currentIndex];
    // Vídeo/áudio sem duration definida tocam até o fim natural — o avanço
    // vem do onEnded do <video>/<audio>. Para esses casos não programamos
    // timer manual nem barra de progresso.
    const usesNaturalDuration =
      (media?.type === "video" || media?.type === "audio") &&
      (media?.duration == null || media?.duration <= 0);

    startTimeRef.current = Date.now();
    setProgress(0);

    if (usesNaturalDuration) {
      return undefined;
    }

    const duration = (media?.duration || 10) * 1000;
    progressRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      setProgress(Math.min(elapsed / duration, 1));
    }, 250);

    const advance = setTimeout(() => advanceMedia("duration_elapsed"), duration);

    return () => {
      clearInterval(progressRef.current);
      clearTimeout(advance);
    };
  }, [phase, currentIndex, playlist, advanceMedia]);

  // ── 6. Poll device commands (sync, refresh_playlist, clear_cache, restart) ──
  // SPEC 003 — comandos destrutivos (restart/shutdown) fazem pre-ACK ANTES de
  // executar, porque o processo do player morre durante a operação e nunca
  // conseguiria mandar o ACK final.
  const pollCommandsRunningRef = useRef(false);

  const pollCommands = useCallback(async () => {
    if (!deviceId || !deviceToken) return;
    if (pollCommandsRunningRef.current) return; // evita reentrância (polling + SSE)
    pollCommandsRunningRef.current = true;
    try {
      const commands = await buscarComandosPendentes(deviceId, deviceToken);
      if (!commands || commands.length === 0) return;

      for (const cmd of commands) {
        const isDestructive = DESTRUCTIVE_COMMANDS.has(cmd.command_type);
        console.log(
          "[player] executing command:",
          cmd.command_type,
          cmd.id,
          isDestructive ? "(destructive)" : "",
        );

        await marcarComandoRecebido(deviceId, cmd.id, deviceToken).catch(() => {});
        await marcarComandoIniciado(deviceId, cmd.id, deviceToken).catch(() => {});

        // Pre-ACK otimista para destrutivos — registra "completed" antes do
        // processo morrer. Se executeCommand falhar (web puro, sem bridge), o
        // bloco abaixo sobrescreve com failed.
        if (isDestructive) {
          await ackComando(
            deviceId,
            cmd.id,
            deviceToken,
            true,
            null,
            {
              platform: Platform.name,
              command_type: cmd.command_type,
              ack_phase: "pre_execution",
              completed_at: new Date().toISOString(),
            },
          ).catch((err) => console.warn("[player] pre-ACK failed:", err));
        }

        const result = await executeCommand(cmd, {
          deviceId,
          setPhase,
          setPlaylist,
          setCurrentIndex,
          setProgress,
        });

        // Não destrutivos: ACK final com resultado real.
        // Destrutivos que falharam ANTES do shutdown (ex: web puro): sobrescreve
        // o pre-ACK otimista com failed.
        if (!isDestructive) {
          await ackComando(
            deviceId,
            cmd.id,
            deviceToken,
            result.success,
            result.errorMessage,
            { ...(result.result || {}), ack_phase: "post_execution" },
          );
        } else if (!result.success) {
          await ackComando(
            deviceId,
            cmd.id,
            deviceToken,
            false,
            result.errorMessage,
            { ...(result.result || {}), ack_phase: "post_execution_override" },
          );
        }

        console.log(
          "[player] command ACK sent:",
          cmd.id,
          result.success ? "success" : "failed",
        );
      }
    } catch (err) {
      console.warn("[player] poll commands error:", err);
    } finally {
      pollCommandsRunningRef.current = false;
    }
  }, [deviceId, deviceToken]);

  useEffect(() => {
    if (!deviceId || !deviceToken) return;
    if (phase !== "playing" && phase !== "no_campaign") return;

    pollCommands();
    pollCommandsRef.current = setInterval(pollCommands, POLL_COMMANDS_INTERVAL);
    return () => clearInterval(pollCommandsRef.current);
  }, [deviceId, deviceToken, phase, pollCommands]);

  // ── 6b. SSE — real-time playlist/config updates ──────────────────────────
  // Conecta após o pareamento e mantém aberto enquanto há credenciais.
  // EventSource reconecta sozinho em falhas transientes (3s default).
  useEffect(() => {
    if (!deviceId || !deviceToken) return;

    const es = abrirStreamPlaylistUpdates(deviceId, deviceToken);
    if (!es) return;
    sseRef.current = es;

    const triggerReload = (label) => {
      console.log("[player] SSE event:", label, "— recarregando playlist");
      setPhase("loading");
    };

    const onSnapshot = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (typeof data.video_muted === "boolean") {
          setVideoMuted(data.video_muted);
        }
      } catch (err) {
        console.warn("[player] SSE snapshot parse error:", err);
      }
    };

    const onPlaylistInvalidated = () => triggerReload("playlist_invalidated");

    // SPEC 003 — comando recém-criado: disparar polling imediato em vez de
    // esperar próximo tick de 10s.
    const onCommandNew = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        console.log("[player] SSE command:new", data?.data || data);
      } catch {
        console.log("[player] SSE command:new");
      }
      // pollCommands() é a função declarada no useEffect anterior; uma ref
      // ou função estável seria mais limpa, mas como é apenas um trigger
      // imediato + o polling já cobre, basta forçar reload da fase de
      // commands via setPhase no mesmo estado (não há side-effect).
      // Aqui invocamos buscarComandosPendentes diretamente.
      buscarComandosPendentes(deviceId, deviceToken).then((commands) => {
        if (commands && commands.length > 0) {
          // O effect 6 (poll) já está agendado e pegará no próximo tick;
          // só precisamos garantir que estamos no estado correto.
          console.log("[player] SSE triggered immediate fetch:", commands.length);
        }
      }).catch((err) => console.warn("[player] SSE command:new fetch error:", err));
    };

    const onError = (err) => {
      // EventSource já tenta reconectar automaticamente.
      console.warn("[player] SSE error:", err);
    };

    // SPEC 004 — revogação remota do pareamento (regenerate, force-repair,
    // token_revoked, device_blocked). Player limpa storage e volta para tela
    // de pareamento sem precisar esperar 401.
    const onPairingRevoked = async (evt) => {
      let reason = "pairing_revoked";
      try {
        const data = JSON.parse(evt.data);
        reason = data?.data?.reason || data?.reason || reason;
      } catch {
        /* ignore */
      }
      console.warn("[player] SSE pairing:revoked", reason);
      try {
        const repair = await import("@/player-core/repair");
        repair.forceRepair(reason);
      } catch (err) {
        console.warn("[player] could not import repair.js:", err);
      }
    };

    es.addEventListener("snapshot", onSnapshot);
    es.addEventListener("playlist_invalidated", onPlaylistInvalidated);
    es.addEventListener("command:new", onCommandNew);
    es.addEventListener("pairing:revoked", onPairingRevoked);
    es.addEventListener("error", onError);

    return () => {
      es.removeEventListener("snapshot", onSnapshot);
      es.removeEventListener("playlist_invalidated", onPlaylistInvalidated);
      es.removeEventListener("command:new", onCommandNew);
      es.removeEventListener("pairing:revoked", onPairingRevoked);
      es.removeEventListener("error", onError);
      es.close();
      sseRef.current = null;
    };
  }, [deviceId, deviceToken]);

  // ── 7. Heartbeat ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!deviceId || !deviceToken) return;
    if (phase !== "playing" && phase !== "no_campaign") return;

    const beat = async () => {
      try {
        const currentMedia = playlist[currentIndex] || null;
        const res = await sendHeartbeat(deviceId, deviceToken, {
          status: phase === "playing" ? "online" : "waiting",
          player_version: PLAYER_VERSION,
          ip_address: null,
          storage_used: 0,
          current_campaign_id: campaignId,
          current_config_version: campaignConfigVersion,
          current_media_id: currentMedia?.id || null,
          current_media_name: currentMedia?.name || null,
          current_audio_track_id: currentAudioTrack?.id || null,
          current_audio_track_name: currentAudioTrack?.name || null,
          current_audio_track_started_at: currentAudioTrack ? trackStartedAtRef.current : null,
          last_error: lastError ? JSON.stringify(lastError).slice(0, 1000) : null,
          playback_status: phase,
        });
        notifyHeartbeatOk();
        console.log("[player] heartbeat:", res);
        if (res?.playlist_updated) setPhase("loading");
      } catch (err) {
        console.warn("[player] heartbeat error:", err);
      }
    };

    beat();
    heartbeatRef.current = setInterval(beat, HEARTBEAT_INTERVAL);
    return () => clearInterval(heartbeatRef.current);
  }, [deviceId, deviceToken, phase, currentIndex, viewsCount, playlist, campaignId, campaignConfigVersion, currentAudioTrack, lastError]);

  // ── SPEC 005: resolver de política de áudio ──────────────────────────────
  const current = playlist[currentIndex] || null;
  const fallbackPolicy = campaign?.audio_policy_default || "auto";
  const audioFadeMs = campaign?.audio_fade_ms ?? 200;

  // spotActive: truthy quando o AudioManager está tocando um spot
  const spotActive = audioManagerCurrent === AUDIO_STATE.SPOT ? { id: "active" } : null;

  const { videoMuted: resolvedVideoMuted, audioEnabled } = useAudioConflictResolver({
    currentMedia: current,
    audioPlaylist,
    currentSpot: spotActive,
    fallbackPolicy,
  });

  // Compat: se a mídia não tem audio_policy_effective (player antigo ou campo ausente),
  // usa o video_muted legado da campanha.
  const finalVideoMuted = current?.audio_policy_effective
    ? resolvedVideoMuted
    : videoMuted;

  // Log de diagnóstico
  useEffect(() => {
    if (!current) return;
    console.log("[player] audio resolver:", {
      media: current.name,
      policy: current.audio_policy_effective,
      has_audio: current.has_audio,
      decision: { videoMuted: finalVideoMuted, audioEnabled },
    });
  }, [current?.id, finalVideoMuted, audioEnabled]);

  // ── Audio Manager: sincroniza fadeMs quando campanha carrega ─────────────
  useEffect(() => {
    const mgr = audioManagerRef.current;
    if (mgr) mgr.state.fadeMs = audioFadeMs;
  }, [audioFadeMs]);

  // ── Audio Manager: carrega playlist no manager quando audioPlaylist muda ──
  useEffect(() => {
    const mgr = audioManagerRef.current;
    if (!mgr) return;
    const rawTracks = audioPlaylist?.tracks || [];
    const tracks = rawTracks.map((t) => ({ ...t, file_url: assetUrl(t.file_url) }));
    const mode = audioPlaylist?.shuffle ? AUDIO_MODE.SHUFFLE : AUDIO_MODE.SEQUENTIAL;
    mgr.loadRadioPlaylist(tracks, mode);
  }, [audioPlaylist?.id, audioPlaylist?.shuffle]);

  // ── Audio Manager: play/stop rádio conforme política + fase ──────────────
  useEffect(() => {
    const mgr = audioManagerRef.current;
    if (!mgr) return;
    if (audioEnabled && phase === "playing") {
      mgr.playRadio().catch(() => {});
    } else {
      mgr.silence().catch(() => {});
    }
  }, [audioEnabled, phase]);

  // ── Audio Manager: agenda de spots ────────────────────────────────────────
  useEffect(() => {
    if (phase !== "playing") return;
    const mgr = audioManagerRef.current;
    if (!mgr) return;

    const spotSchedules = audioPlaylist?.spot_schedules;
    if (!spotSchedules?.length) return;

    const timers = [];

    spotSchedules.forEach((sched) => {
      if (!sched.file_url || !sched.interval_seconds) return;

      const now = new Date();
      const hhmm = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
      const inWindow =
        (!sched.start_time || hhmm >= sched.start_time) &&
        (!sched.end_time || hhmm <= sched.end_time);

      if (!inWindow) return;

      const intervalMs = sched.interval_seconds * 1000;
      const url = assetUrl(sched.file_url);
      const policy = sched.insertion_policy || "interrupt";

      const id = setInterval(() => {
        const nowCheck = new Date();
        const t = `${String(nowCheck.getHours()).padStart(2, "0")}:${String(nowCheck.getMinutes()).padStart(2, "0")}`;
        const stillInWindow =
          (!sched.start_time || t >= sched.start_time) &&
          (!sched.end_time || t <= sched.end_time);
        if (!stillInWindow) return;
        console.log("[player] spot scheduled:", sched.spot_name || sched.spot_id);
        mgr.playSpot(url, policy).catch(() => {});
      }, intervalMs);

      timers.push(id);
    });

    return () => timers.forEach(clearInterval);
  }, [audioPlaylist?.id, phase]);

  // `current` já declarado acima no bloco do resolver SPEC 005
  const nextMedia = playlist.length ? playlist[(currentIndex + 1) % playlist.length] : null;
  const debugData = {
    enabled: debugMode,
    deviceId,
    pairingCode,
    platform: Platform.name,
    isCapacitor: Platform.isCapacitor,
    isOnline,
    phase,
    campaignId,
    campaignConfigVersion,
    currentIndex,
    totalItems: playlist.length,
    schedule: campaignSchedule,
    loopsCompleted,
    media: current,
    nextMedia,
    video: videoDebug,
    lastError,
    lastSync,
  };

  if (phase === "waiting") {
    return (
      <>
        <PairingScreen pairingCode={pairingCode} apiStatus={apiStatus} forceRepairReason={forceRepairReason} />
        <PlayerDebugOverlay data={debugData} />
      </>
    );
  }

  if (phase === "loading") {
    if (current) {
      return (
        <div className="fixed inset-0 bg-black">
          <MediaRenderer
            media={current}
            progress={progress}
            videoMuted={finalVideoMuted}
            onDebug={setVideoDebug}
            onError={handleMediaError}
            onEnded={advanceMedia}
          />
          <PlayerOSD
            media={current}
            totalItems={playlist.length}
            currentIndex={currentIndex}
            deviceName={deviceName}
            currentAudioTrack={currentAudioTrack}
            audioEnabled={audioEnabled && phase === "playing"}
            osdConfig={osdConfig}
          />
          <div className="absolute inset-0 flex items-center justify-center bg-black/25 text-white text-sm">
            Sincronizando playlist...
          </div>
          <PlayerDebugOverlay data={debugData} />
        </div>
      );
    }
    return (
      <>
        <LoadingScreen message="Carregando playlist..." />
        <PlayerDebugOverlay data={debugData} />
      </>
    );
  }

  if (phase === "error") {
    return (
      <>
        <ErrorScreen
          onRetry={() => {
            PairingStorage.clear();
            setDeviceId(null);
            setDeviceToken(null);
            setPhase("waiting");
          }}
        />
        <PlayerDebugOverlay data={debugData} />
      </>
    );
  }

  // Device is paired but no active campaign yet
  if (phase === "no_campaign") {
    return (
      <>
        <div className="fixed inset-0 bg-[#07090f] flex flex-col items-center justify-center text-white gap-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-600/20 flex items-center justify-center">
            <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3" />
            </svg>
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold">{deviceName || "Dispositivo pareado"}</p>
            <p className="text-sm text-white/40 mt-1">Aguardando campanha ativa...</p>
            <p className="text-xs text-white/20 mt-3">O player verifica automaticamente a cada 30s</p>
          </div>
        </div>
        <PlayerDebugOverlay data={debugData} />
      </>
    );
  }

  return (
    <div className="fixed inset-0 bg-black">
      <MediaRenderer
        media={current}
        progress={progress}
        videoMuted={finalVideoMuted}
        onDebug={setVideoDebug}
        onError={handleMediaError}
        onEnded={advanceMedia}
      />
      <PlayerOSD
        media={current}
        totalItems={playlist.length}
        currentIndex={currentIndex}
        deviceName={deviceName}
        currentAudioTrack={currentAudioTrack}
        audioEnabled={audioEnabled && phase === "playing"}
        osdConfig={osdConfig}
      />
      <PlayerDebugOverlay data={debugData} />
    </div>
  );
}
