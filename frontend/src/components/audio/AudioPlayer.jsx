import { useEffect, useRef, useState, useCallback } from "react";
import { assetUrl } from "@/utils/mediaUtils";

/**
 * AudioPlayer — Motor de áudio persistente.
 *
 * REGRAS DE SOBREVIVÊNCIA:
 * 1. NUNCA desmontar este componente — ele deve viver pelo ciclo de vida
 *    inteiro do Player.jsx.
 * 2. Play/pause são controlados pela prop `enabled`, nunca por desmontagem.
 * 3. O elemento <audio> é criado UMA vez e reutilizado indefinidamente.
 * 4. Quando `enabled=false`, apenas pausamos. Quando `enabled=true`, tentamos
 *    retomar.
 * 5. Erros de autoplay são logados e capturados silenciosamente.
 *
 * Props:
 *   audioPlaylist - Dados da playlist com tracks inline
 *   enabled       - Se o áudio deve estar ativo (play) ou pausado
 *   onStatusChange - Callback de status
 */
export default function AudioPlayer({ audioPlaylist, enabled = true, onStatusChange }) {
  const audioRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const currentIndexRef = useRef(0);
  const tracksRef = useRef([]);
  const isPlayingRef = useRef(false);

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
      return;
    }

    tracksRef.current = tracks;
    console.log("[AudioPlayer] playlist updated:", tracks.length, "tracks");

    if (!tracks.length) {
      console.log("[AudioPlayer] empty playlist, pausing");
      audioRef.current?.pause();
      return;
    }

    // Só reseta índice se for playlist diferente
    console.log("[AudioPlayer] resetting to track 0");
    setCurrentIndex(0);
    currentIndexRef.current = 0;
  }, [audioPlaylist?.id]);

  // ── 3. Toca/pausa baseado em `enabled` e `currentIndex` ─────────────────
  const handleError = useCallback(() => {
    console.warn("[AudioPlayer] error on track", currentIndexRef.current);
    const tracks = tracksRef.current;
    if (!tracks.length) return;
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

  // ── 4. Log de mudança de enabled ───────────────────────────────────────
  useEffect(() => {
    console.log("[AudioPlayer] enabled changed to:", enabled);
    const audio = audioRef.current;
    if (!audio) return;

    if (enabled && audio.paused && tracksRef.current.length > 0) {
      console.log("[AudioPlayer] auto-resuming after enabled=true");
      audio.play().catch((err) => {
        console.warn("[AudioPlayer] auto-resume failed:", err.name);
      });
    } else if (!enabled && !audio.paused) {
      console.log("[AudioPlayer] auto-pausing after enabled=false");
      audio.pause();
    }
  }, [enabled]);

  // Componente invisível — motor de áudio persistente
  return null;
}
