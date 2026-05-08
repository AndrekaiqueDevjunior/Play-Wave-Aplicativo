import React, { useState, useEffect, useRef } from "react";
import {
  isApiConfigured,
  pairRequest,
  getPairStatus,
  getDevicePlaylist,
  sendHeartbeat,
} from "@/lib/api";
import AudioPlayer from "@/components/audio/AudioPlayer";
import PairingScreen from "@/components/player/PairingScreen";
import LoadingScreen from "@/components/player/LoadingScreen";
import ErrorScreen from "@/components/player/ErrorScreen";
import MediaRenderer from "@/components/player/MediaRenderer";
import PlayerOSD from "@/components/player/PlayerOSD";

const HEARTBEAT_INTERVAL = 30_000;
const POLL_INTERVAL = 3_000;
const PLAYER_VERSION = "3.1.0";

function generateCode() {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  return (
    "TV-" +
    Array.from(
      { length: 4 },
      () => chars[Math.floor(Math.random() * chars.length)],
    ).join("")
  );
}

export default function Player() {
  const [pairingCode] = useState(() => generateCode());
  const [phase, setPhase] = useState("waiting"); // waiting | loading | playing | error
  const [deviceId, setDeviceId] = useState(null);
  const [deviceName, setDeviceName] = useState("");
  const [playlist, setPlaylist] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [viewsCount, setViewsCount] = useState(0);
  const [apiStatus, setApiStatus] = useState(
    isApiConfigured() ? "connecting" : "no_api",
  );

  const pollRef = useRef(null);
  const heartbeatRef = useRef(null);
  const progressRef = useRef(null);
  const startTimeRef = useRef(null);

  // ── 1. Registra no FastAPI ─────────────────────────────────────────────
  useEffect(() => {
    if (!isApiConfigured()) {
      setApiStatus("no_api");
      return;
    }
    pairRequest({
      pairing_code: pairingCode,
      player_version: PLAYER_VERSION,
      os: "Web Player",
    })
      .then(() => setApiStatus("connected"))
      .catch(() => setApiStatus("error"));
  }, [pairingCode]);

  // ── 2. Polling de pareamento ─────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "waiting" || !isApiConfigured()) return;

    const poll = async () => {
      const res = await getPairStatus(pairingCode);
      if (res?.status === "paired") {
        setDeviceId(res.device_id);
        setPhase("loading");
      }
    };

    pollRef.current = setInterval(poll, POLL_INTERVAL);
    poll();
    return () => clearInterval(pollRef.current);
  }, [phase, pairingCode]);

  // ── 3. Carrega playlist ───────────────────────────────────────────────────
  useEffect(() => {
    if (phase !== "loading" || !deviceId) return;

    const load = async () => {
      const res = await getDevicePlaylist(deviceId);
      const medias = res?.media || [];
      if (res?.device_name) setDeviceName(res.device_name);

      if (medias.length > 0) {
        setPlaylist(medias);
        setCurrentIndex(0);
        setProgress(0);
        setPhase("playing");
      } else {
        setPhase("waiting");
      }
    };

    load().catch(() => setPhase("error"));
  }, [phase, deviceId]);

  // ── 4. Progresso + avanço de mídia ───────────────────────────────────────
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
      setCurrentIndex((prev) => (prev + 1) % playlist.length);
      setViewsCount((prev) => prev + 1);
    }, duration);

    return () => {
      clearInterval(progressRef.current);
      clearTimeout(advance);
    };
  }, [phase, currentIndex, playlist]);

  // ── 5. Heartbeat ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!deviceId || phase !== "playing") return;

    const beat = async () => {
      const res = await sendHeartbeat(deviceId, {
        status: "online",
        current_media_id: playlist[currentIndex]?.id || null,
        views_count: viewsCount,
      });
      if (res?.playlist_updated) setPhase("loading");
    };

    heartbeatRef.current = setInterval(beat, HEARTBEAT_INTERVAL);
    return () => clearInterval(heartbeatRef.current);
  }, [deviceId, phase, currentIndex, viewsCount, playlist]);

  // ── Renders ───────────────────────────────────────────────────────────────
  if (phase === "waiting") {
    return <PairingScreen pairingCode={pairingCode} apiStatus={apiStatus} />;
  }

  if (phase === "loading") {
    return <LoadingScreen message="Carregando playlist..." />;
  }

  if (phase === "error") {
    return <ErrorScreen onRetry={() => setPhase("waiting")} />;
  }

  const current = playlist[currentIndex];
  return (
    <div className="fixed inset-0 bg-black">
      <MediaRenderer
        media={current}
        progress={progress}
        onEnded={() => setCurrentIndex((prev) => (prev + 1) % playlist.length)}
      />
      <PlayerOSD
        media={current}
        totalItems={playlist.length}
        currentIndex={currentIndex}
        deviceName={deviceName}
      />
      {deviceId && <AudioPlayer deviceId={deviceId} />}
    </div>
  );
}
