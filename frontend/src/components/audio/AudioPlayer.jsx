import { useEffect, useRef, useState, useCallback } from "react";
import { assetUrl } from "@/utils/mediaUtils";
import PlaybackQueueManager from "@/player-core/playbackQueueManager";

const FADE_INTERVAL_MS = 25;

/**
 * Sobe/desce volume de um elemento <audio> suavemente.
 * Retorna o intervalId (ou null se durationMs <= 0).
 */
function doFade(audio, targetVolume, durationMs, onComplete) {
  if (durationMs <= 0) {
    audio.volume = Math.max(0, Math.min(1, targetVolume));
    onComplete?.();
    return null;
  }
  const steps = Math.max(1, Math.floor(durationMs / FADE_INTERVAL_MS));
  const delta = (targetVolume - audio.volume) / steps;
  let step = 0;
  const id = setInterval(() => {
    step += 1;
    audio.volume = Math.max(0, Math.min(1, audio.volume + delta));
    if (step >= steps) {
      audio.volume = Math.max(0, Math.min(1, targetVolume));
      clearInterval(id);
      onComplete?.();
    }
  }, FADE_INTERVAL_MS);
  return id;
}

/**
 * AudioPlayer — Motor de áudio persistente.
 *
 * REGRAS DE SOBREVIVÊNCIA:
 * 1. NUNCA desmontar este componente — ele deve viver pelo ciclo de vida
 *    inteiro do Player.jsx.
 * 2. Play/pause são controlados pela prop `enabled`, nunca por desmontagem.
 * 3. O elemento <audio> é criado UMA vez e reutilizado indefinidamente.
 * 4. Quando `enabled=false`, fade out e pausa. Quando `enabled=true`, play com fade in.
 * 5. Erros de autoplay são logados e capturados silenciosamente.
 *
 * Props:
 *   audioPlaylist  — Dados da playlist com tracks inline
 *   enabled        — Se o áudio deve estar ativo (play) ou pausado
 *   fadeMs         — Duração do fade em ms (SPEC 005, default 200)
 *   onStatusChange — Callback de status
 *   onTrackChange  — Callback debounced para reportar faixa atual ao backend
 */
export default function AudioPlayer({
  audioPlaylist,
  enabled = true,
  fadeMs = 200,
  onStatusChange,
  onTrackChange,
}) {
  const audioRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const currentIndexRef = useRef(0);
  const tracksRef = useRef([]);
  const isPlayingRef = useRef(false);
  const fadeIdRef = useRef(null);  // SPEC 005: cancelar fade anterior
  const trackChangeDebounceRef = useRef(null);
  const lastReportedTrackIdRef = useRef(null);
  const queueManagerRef = useRef(null);  // TASK 06: gerenciar fila com shuffle/loop

  // ── 1. Cria o elemento <audio> UMA vez, nunca o recria ──────────────────
  useEffect(() => {
    console.log("[AudioPlayer] 🎵 mount — creating persistent <audio> element");
    const audio = document.createElement("audio");
    audio.preload = "auto";
    audioRef.current = audio;

    return () => {
      console.log("[AudioPlayer] 💀 unmount — pausing and cleaning up");
      audio.pause();
      audio.src = "";
      audioRef.current = null;
    };
  }, []);

  // ── 2. Atualiza tracks quando playlist muda ────────────────────────────
  useEffect(() => {
    const tracks = audioPlaylist?.tracks || [];
    const prevTracks = tracksRef.current;

    // Verifica se a playlist realmente mudou (não apenas re-render)
    const samePlaylist =
      prevTracks.length === tracks.length &&
      tracks.length > 0 &&
      prevTracks[0]?.id === tracks[0]?.id;

    if (samePlaylist) {
      console.log("[AudioPlayer] playlist unchanged, skipping reset");
      // Mas atualizar opções de playback se mudaram
      if (queueManagerRef.current) {
        queueManagerRef.current.updateOptions({
          shuffle_enabled: audioPlaylist?.shuffle_enabled ?? false,
          loop_enabled: audioPlaylist?.loop_enabled ?? true,
          playback_mode: audioPlaylist?.playback_mode ?? 'sequential',
        });
      }
      return;
    }

    tracksRef.current = tracks;
    console.log("[AudioPlayer] playlist updated:", tracks.length, "tracks");

    if (!tracks.length) {
      console.log("[AudioPlayer] empty playlist, pausing");
      audioRef.current?.pause();
      lastReportedTrackIdRef.current = null;
      queueManagerRef.current = null;
      onTrackChange?.(null);
      return;
    }

    // TASK 06: Inicializar QueueManager com opções de playback
    queueManagerRef.current = new PlaybackQueueManager(tracks, {
      shuffle_enabled: audioPlaylist?.shuffle_enabled ?? false,
      loop_enabled: audioPlaylist?.loop_enabled ?? true,
      playback_mode: audioPlaylist?.playback_mode ?? 'sequential',
    });

    console.log("[AudioPlayer] QueueManager initialized", queueManagerRef.current.getQueueInfo());

    // Obter primeira faixa do queue
    const firstTrack = queueManagerRef.current.getNext();
    if (firstTrack && tracksRef.current.some(t => t.id === firstTrack.id)) {
      const idx = tracksRef.current.findIndex(t => t.id === firstTrack.id);
      console.log("[AudioPlayer] starting from track index:", idx);
      setCurrentIndex(idx);
      currentIndexRef.current = idx;
    } else {
      console.log("[AudioPlayer] resetting to track 0");
      setCurrentIndex(0);
      currentIndexRef.current = 0;
    }
  }, [audioPlaylist?.id]);

  // ── SPEC 006: reporta faixa atual com debounce ─────────────────────────
  useEffect(() => {
    const track = tracksRef.current[currentIndex] || null;
    const trackId = track?.id || null;

    if (!enabled) {
      return;
    }
    if (lastReportedTrackIdRef.current === trackId) {
      return;
    }

    if (trackChangeDebounceRef.current) {
      clearTimeout(trackChangeDebounceRef.current);
    }
    trackChangeDebounceRef.current = setTimeout(() => {
      lastReportedTrackIdRef.current = trackId;
      onTrackChange?.(track);
      trackChangeDebounceRef.current = null;
    }, 500);

    return () => {
      if (trackChangeDebounceRef.current) {
        clearTimeout(trackChangeDebounceRef.current);
        trackChangeDebounceRef.current = null;
      }
    };
  }, [audioPlaylist?.id, currentIndex, enabled, onTrackChange]);

  useEffect(() => {
    if (!enabled && lastReportedTrackIdRef.current !== null) {
      if (trackChangeDebounceRef.current) {
        clearTimeout(trackChangeDebounceRef.current);
        trackChangeDebounceRef.current = null;
      }
      lastReportedTrackIdRef.current = null;
      onTrackChange?.(null);
    }
  }, [enabled, onTrackChange]);

  // ── 3. Toca/pausa baseado em `enabled` e `currentIndex` ─────────────────
  const handleError = useCallback(() => {
    console.warn("[AudioPlayer] error on track", currentIndexRef.current);
    const tracks = tracksRef.current;
    if (!tracks.length) return;

    // TASK 06: Usar QueueManager para obter próxima faixa
    if (queueManagerRef.current) {
      const nextTrack = queueManagerRef.current.skipToNext();
      if (nextTrack) {
        const nextIndex = tracks.findIndex(t => t.id === nextTrack.id);
        if (nextIndex >= 0) {
          currentIndexRef.current = nextIndex;
          setCurrentIndex(nextIndex);
          return;
        }
      }
    }

    // Fallback para comportamento legado
    const next = currentIndexRef.current + 1;
    if (next < tracks.length) {
      currentIndexRef.current = next;
      setCurrentIndex(next);
    } else if (audioPlaylist?.loop) {
      currentIndexRef.current = 0;
      setCurrentIndex(0);
    }
  }, [audioPlaylist]);

  const handleEnded = useCallback(() => {
    console.log("[AudioPlayer] track ended:", currentIndexRef.current);
    const tracks = tracksRef.current;
    if (!tracks.length) return;

    // TASK 06: Usar QueueManager para obter próxima faixa
    if (queueManagerRef.current) {
      const nextTrack = queueManagerRef.current.skipToNext();
      if (nextTrack) {
        const nextIndex = tracks.findIndex(t => t.id === nextTrack.id);
        if (nextIndex >= 0) {
          currentIndexRef.current = nextIndex;
          setCurrentIndex(nextIndex);
          return;
        }
      } else {
        // Fila terminou e não tem loop
        console.log("[AudioPlayer] queue finished, no loop");
        return;
      }
    }

    // Fallback para comportamento legado se não houver QueueManager
    const next = currentIndexRef.current + 1;
    if (next < tracks.length) {
      currentIndexRef.current = next;
      setCurrentIndex(next);
    } else if (audioPlaylist?.loop) {
      currentIndexRef.current = 0;
      setCurrentIndex(0);
    }
  }, [audioPlaylist]);

  useEffect(() => {
    const audio = audioRef.current;
    const tracks = tracksRef.current;
    if (!audio || !tracks.length || !audioPlaylist) return;

    const track = tracks[currentIndex];
    if (!track?.file_url) return;

    // Remove listeners antigos para evitar duplicação
    audio.removeEventListener("ended", handleEnded);
    audio.removeEventListener("error", handleError);

    const newSrc = assetUrl(track.file_url);
    const needsReload = audio.src !== newSrc;

    if (needsReload) {
      console.log("[AudioPlayer] loading track", currentIndex, track.name || track.id);
      audio.src = newSrc;
      audio.volume = track.volume ?? audioPlaylist.volume ?? 0.7;
    } else {
      console.log("[AudioPlayer] same src, reusing");
    }

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    if (enabled) {
      console.log("[AudioPlayer] attempting play (enabled=true)");
      audio.play().then(() => {
        console.log("[AudioPlayer] ▶️ playing track", currentIndex);
        isPlayingRef.current = true;
      }).catch((err) => {
        console.warn("[AudioPlayer] ⛔ autoplay blocked:", err.name, err.message);
        isPlayingRef.current = false;
      });
    } else {
      console.log("[AudioPlayer] ⏸️ pausing (enabled=false)");
      audio.pause();
      isPlayingRef.current = false;
    }

    onStatusChange?.({ playing: enabled, track, index: currentIndex });

    return () => {
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, [currentIndex, audioPlaylist, enabled, handleEnded, handleError, onStatusChange]);

  // ── 4. SPEC 005: fade ao mudar enabled ────────────────────────────────
  useEffect(() => {
    console.log("[AudioPlayer] enabled changed to:", enabled, "fadeMs:", fadeMs);
    const audio = audioRef.current;
    if (!audio) return;

    // Cancela fade em andamento
    if (fadeIdRef.current) {
      clearInterval(fadeIdRef.current);
      fadeIdRef.current = null;
    }

    if (enabled && tracksRef.current.length > 0) {
      if (audio.paused) {
        audio.volume = 0;
        audio.play().catch((err) => {
          console.warn("[AudioPlayer] auto-resume failed:", err.name);
        });
      }
      const targetVol = tracksRef.current[currentIndexRef.current]?.volume
        ?? audioPlaylist?.volume
        ?? 0.7;
      fadeIdRef.current = doFade(audio, targetVol, fadeMs, () => {
        fadeIdRef.current = null;
      });
    } else if (!enabled && !audio.paused) {
      fadeIdRef.current = doFade(audio, 0, fadeMs, () => {
        audio.pause();
        fadeIdRef.current = null;
      });
    }

    return () => {
      if (fadeIdRef.current) {
        clearInterval(fadeIdRef.current);
        fadeIdRef.current = null;
      }
    };
  }, [enabled, fadeMs]);

  // Componente invisível — motor de áudio persistente
  return null;
}
