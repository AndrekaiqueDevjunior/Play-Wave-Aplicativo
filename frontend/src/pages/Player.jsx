import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  isApiConfigured,
  pairRequest,
  getPairStatus,
  getDevicePlaylist,
  sendHeartbeat,
} from "@/lib/api";
import {
  registrarPlayback,
  buscarComandosPendentes,
  ackComando,
  abrirStreamPlaylistUpdates,
} from "@/api/dispositivos";
import AudioPlayer from "@/components/audio/AudioPlayer";
import PairingScreen from "@/components/player/PairingScreen";
import LoadingScreen from "@/components/player/LoadingScreen";
import ErrorScreen from "@/components/player/ErrorScreen";
import MediaRenderer from "@/components/player/MediaRenderer";
import PlayerOSD from "@/components/player/PlayerOSD";
import { assetUrl } from "@/utils/mediaUtils";

const HEARTBEAT_INTERVAL = 30_000;
const POLL_PAIRING_INTERVAL = 3_000;
const POLL_PLAYLIST_INTERVAL = 30_000;
const POLL_COMMANDS_INTERVAL = 10_000;
const PLAYER_VERSION = "3.1.0";

const LS_CODE  = "pw_player_code";
const LS_ID    = "pw_player_device_id";
const LS_TOKEN = "pw_player_device_token";

function generateCode() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  return (
    "TV-" +
    Array.from({ length: 4 }, () => chars[Math.floor(Math.random() * chars.length)]).join("")
  );
}

function loadSavedPairing() {
  return {
    code:  localStorage.getItem(LS_CODE)  || null,
    id:    localStorage.getItem(LS_ID)    || null,
    token: localStorage.getItem(LS_TOKEN) || null,
  };
}

function savePairing(code, id, token) {
  localStorage.setItem(LS_CODE,  code);
  localStorage.setItem(LS_ID,    id);
  localStorage.setItem(LS_TOKEN, token);
}

function clearPairing() {
  [LS_CODE, LS_ID, LS_TOKEN].forEach((k) => localStorage.removeItem(k));
}

export default function Player() {
  const saved = loadSavedPairing();

  // Generate or reuse pairing code
  const [pairingCode] = useState(() => saved.code || generateCode());

  // If we already have device credentials, start in "loading" to skip pairing
  const [phase, setPhase] = useState(
    () => (saved.id && saved.token ? "loading" : "waiting"),
  );

  const [deviceId,    setDeviceId]    = useState(saved.id);
  const [deviceToken, setDeviceToken] = useState(saved.token);
  const [deviceName,  setDeviceName]  = useState("");
  const [playlist,    setPlaylist]    = useState([]);
  const [audioPlaylist, setAudioPlaylist] = useState(null);
  const [campaignId, setCampaignId] = useState(null);
  const [videoMuted, setVideoMuted] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress,   setProgress]    = useState(0);
  const [viewsCount, setViewsCount]  = useState(0);
  const [apiStatus,  setApiStatus]   = useState(
    isApiConfigured() ? "connecting" : "no_api",
  );

  const pollPairRef      = useRef(null);
  const pollPlaylistRef  = useRef(null);
  const pollCommandsRef  = useRef(null);
  const heartbeatRef     = useRef(null);
  const progressRef      = useRef(null);
  const startTimeRef     = useRef(null);
  const deviceTokenRef   = useRef(deviceToken);
  const sseRef           = useRef(null);

  // Keep ref in sync so callbacks always have the latest token
  useEffect(() => { deviceTokenRef.current = deviceToken; }, [deviceToken]);

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
          savePairing(pairingCode, res.device_id, res.device_token);
          setDeviceId(res.device_id);
          setDeviceToken(res.device_token);
          deviceTokenRef.current = res.device_token;
          setPhase("loading");
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

      const medias = (res?.media || []).map((m) => ({
        ...m,
        file_url: assetUrl(m.file_url),
      }));

      if (res?.campaign?.id) {
        setCampaignId(res.campaign.id);
      }
      setVideoMuted(res?.campaign?.video_muted !== false);
      setAudioPlaylist(res?.audio_playlist || null);

      if (medias.length > 0) {
        setPlaylist(medias);
        setCurrentIndex(0);
        setProgress(0);
        setPhase("playing");
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
    }).catch((err) => {
      const msg = err?.message || "";
      const isAuthError = msg.includes("401") || msg.includes("403") || msg.includes("Token");
      if (isAuthError) {
        console.error("[player] auth error, clearing saved pairing:", msg);
        clearPairing();
        setDeviceId(null);
        setDeviceToken(null);
        setPhase("waiting");
      } else {
        console.error("[player] playlist load failed (server error), entering no_campaign:", msg);
        setPhase("no_campaign");
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

  // ── 5. Progress + media advance ──────────────────────────────────────────
  useEffect(() => {
    if (phase !== "playing" || playlist.length === 0) return;
    const duration = (playlist[currentIndex]?.duration || 10) * 1000;
    startTimeRef.current = Date.now();
    setProgress(0);

    progressRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      setProgress(Math.min(elapsed / duration, 1));
    }, 250);

    const advance = setTimeout(() => {
      const prevIndex = currentIndex;
      const prevMedia = playlist[prevIndex];
      if (prevMedia && campaignId && deviceToken) {
        registrarPlayback(deviceId, deviceToken, {
          campaign_id: campaignId,
          media_id: prevMedia.id,
          started_at: new Date(Date.now() - duration).toISOString(),
          ended_at: new Date().toISOString(),
          duration_ms: duration,
          status: "completed",
        }).catch(() => {});
      }
      setCurrentIndex((prev) => (prev + 1) % playlist.length);
      setViewsCount((prev) => prev + 1);
    }, duration);

    return () => {
      clearInterval(progressRef.current);
      clearTimeout(advance);
    };
  }, [phase, currentIndex, playlist]);

  // ── 6. Poll device commands (sync, refresh_playlist, clear_cache, restart) ──
  useEffect(() => {
    if (!deviceId || !deviceToken) return;
    if (phase !== "playing" && phase !== "no_campaign") return;

    const pollCommands = async () => {
      try {
        const commands = await buscarComandosPendentes(deviceId, deviceToken);
        if (!commands || commands.length === 0) return;

        for (const cmd of commands) {
          console.log("[player] executing command:", cmd.command_type, cmd.id);
          let success = true;
          let errorMessage = null;

          try {
            switch (cmd.command_type) {
              case "sync":
                console.log("[player] command: sync");
                setPhase("loading");
                break;
              case "refresh_playlist":
                console.log("[player] command: refresh_playlist");
                setPhase("loading");
                break;
              case "clear_cache":
                console.log("[player] command: clear_cache");
                setPlaylist([]);
                setPhase("loading");
                break;
              case "restart":
                // Soft restart: reseta o estado do app sem reload da página.
                // Reload duro mata o "user activation" do navegador e o vídeo
                // volta a tocar mudo (política de autoplay com som). O soft
                // restart preserva o ciclo de vida da aba e o som continua.
                console.log("[player] command: restart (soft reset)");
                setPlaylist([]);
                setCurrentIndex(0);
                setProgress(0);
                setPhase("loading");
                break;
              default:
                console.warn("[player] unknown command:", cmd.command_type);
            }
          } catch (execErr) {
            success = false;
            errorMessage = execErr?.message || String(execErr);
            console.error("[player] command execution failed:", errorMessage);
          }

          await ackComando(deviceId, cmd.id, deviceToken, success, errorMessage);
          console.log("[player] command ACK sent:", cmd.id, success ? "success" : "failed");
        }
      } catch (err) {
        console.warn("[player] poll commands error:", err);
      }
    };

    pollCommands();
    pollCommandsRef.current = setInterval(pollCommands, POLL_COMMANDS_INTERVAL);
    return () => clearInterval(pollCommandsRef.current);
  }, [deviceId, deviceToken, phase]);

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
    const onError = (err) => {
      // EventSource já tenta reconectar automaticamente.
      console.warn("[player] SSE error:", err);
    };

    es.addEventListener("snapshot", onSnapshot);
    es.addEventListener("playlist_invalidated", onPlaylistInvalidated);
    es.addEventListener("error", onError);

    return () => {
      es.removeEventListener("snapshot", onSnapshot);
      es.removeEventListener("playlist_invalidated", onPlaylistInvalidated);
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
        const res = await sendHeartbeat(deviceId, deviceToken, {
          status: phase === "playing" ? "online" : "waiting",
          player_version: PLAYER_VERSION,
          ip_address: null,
          storage_used: 0,
          current_campaign_id: campaignId,
          current_media_name: playlist[currentIndex]?.name || null,
        });
        console.log("[player] heartbeat:", res);
        if (res?.playlist_updated) setPhase("loading");
      } catch (err) {
        console.warn("[player] heartbeat error:", err);
      }
    };

    beat();
    heartbeatRef.current = setInterval(beat, HEARTBEAT_INTERVAL);
    return () => clearInterval(heartbeatRef.current);
  }, [deviceId, deviceToken, phase, currentIndex, viewsCount, playlist, campaignId]);

  // ── Renders ───────────────────────────────────────────────────────────────
  // AudioPlayer NUNCA desmonta — vive pelo ciclo inteiro do app.
  // `enabled` controla play/pause; `audioPlaylist` controla o conteúdo.
  const renderAudio = () => (
    <AudioPlayer
      audioPlaylist={audioPlaylist || null}
      enabled={phase === "playing"}
      onStatusChange={(status) =>
        console.log("[player] audio status:", status.playing, status.track?.name)
      }
    />
  );

  if (phase === "waiting") {
    return (
      <>
        {renderAudio()}
        <PairingScreen pairingCode={pairingCode} apiStatus={apiStatus} />
      </>
    );
  }

  if (phase === "loading") {
    return (
      <>
        {renderAudio()}
        <LoadingScreen message="Carregando playlist..." />
      </>
    );
  }

  if (phase === "error") {
    return (
      <>
        {renderAudio()}
        <ErrorScreen
          onRetry={() => {
            clearPairing();
            setDeviceId(null);
            setDeviceToken(null);
            setPhase("waiting");
          }}
        />
      </>
    );
  }

  // Device is paired but no active campaign yet
  if (phase === "no_campaign") {
    return (
      <>
        {renderAudio()}
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
      </>
    );
  }

  const current = playlist[currentIndex];
  return (
    <div className="fixed inset-0 bg-black">
      <MediaRenderer
        media={current}
        progress={progress}
        videoMuted={videoMuted}
        onEnded={() => setCurrentIndex((prev) => (prev + 1) % playlist.length)}
      />
      <PlayerOSD
        media={current}
        totalItems={playlist.length}
        currentIndex={currentIndex}
        deviceName={deviceName}
      />
      {renderAudio()}
    </div>
  );
}
