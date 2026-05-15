import { useEffect, useRef, useState, useCallback } from "react";
import { assetUrl } from "@/utils/mediaUtils";

/**
 * AudioPlayer — Motor de áudio independente do motor visual.
 * Toca playlist MP3 em paralelo à campanha visual.
 * Não reinicia quando a mídia visual troca.
 *
 * @param {Object} audioPlaylist - Dados da playlist com tracks inline:
 *   { id, name, volume, loop, shuffle, tracks: [{id, name, file_url, duration_seconds, volume}] }
 */
export default function AudioPlayer({ audioPlaylist, onStatusChange }) {
  const audioRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const currentIndexRef = useRef(0);
  const tracksRef = useRef([]);

  // Reseta quando a playlist muda
  useEffect(() => {
    if (!audioPlaylist?.tracks?.length) return;
    tracksRef.current = audioPlaylist.tracks;
    setCurrentIndex(0);
    currentIndexRef.current = 0;
  }, [audioPlaylist?.id]);

  // Inicializa o elemento de áudio
  useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.preload = "auto";

    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
    };
  }, []);

  const handleError = useCallback(() => {
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

  // Toca a faixa atual quando index muda
  useEffect(() => {
    const tracks = tracksRef.current;
    if (!audioRef.current || !tracks.length || !audioPlaylist) return;

    const track = tracks[currentIndex];
    if (!track?.file_url) return;

    const audio = audioRef.current;
    audio.removeEventListener("ended", handleEnded);
    audio.removeEventListener("error", handleError);

    audio.src = assetUrl(track.file_url);
    audio.volume = track.volume ?? audioPlaylist.volume ?? 0.7;

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    audio.play().catch(() => {
      // autoplay bloqueado — aguarda interação do usuário
    });

    onStatusChange?.({ playing: true, track, index: currentIndex });
  }, [currentIndex, audioPlaylist, handleEnded, handleError, onStatusChange]);

  // Componente invisível — só lógica
  return null;
}
