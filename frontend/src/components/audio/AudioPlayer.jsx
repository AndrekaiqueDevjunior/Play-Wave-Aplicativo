import { useEffect, useRef, useState, useCallback } from "react";
import { buscarDispositivo } from "@/api/dispositivos";
import { buscarPlaylistAudio, listarFaixas } from "@/api/audio";
import { assetUrl } from "@/utils/mediaUtils";

/**
 * AudioPlayer — Motor de áudio independente do motor visual.
 * Toca playlist MP3 em paralelo à campanha visual.
 * Não reinicia quando a mídia visual troca.
 */
export default function AudioPlayer({ deviceId, onStatusChange }) {
  const audioRef = useRef(null);
  const [playlist, setPlaylist] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const currentIndexRef = useRef(0);

  // Busca playlist vinculada ao dispositivo
  useEffect(() => {
    if (!deviceId) return;

    const loadPlaylist = async () => {
      const device = await buscarDispositivo(deviceId);
      if (!device?.audio_playlist_id) return;

      const pl = await buscarPlaylistAudio(device.audio_playlist_id);
      if (!pl || pl.status !== "active") return;

      if (!pl.track_ids?.length) return;

      const allTracks = await listarFaixas();
      const ordered = pl.track_ids
        .map((id) => allTracks.find((t) => t.id === id))
        .filter((t) => t && t.status === "active");

      setPlaylist(pl);
      setTracks(ordered);
      setCurrentIndex(0);
      currentIndexRef.current = 0;
    };

    loadPlaylist();
  }, [deviceId]);

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
    // Pula faixa corrompida/indisponível
    const next = currentIndexRef.current + 1;
    if (next < tracks.length) {
      currentIndexRef.current = next;
      setCurrentIndex(next);
    } else if (playlist?.loop_enabled) {
      currentIndexRef.current = 0;
      setCurrentIndex(0);
    }
  }, [tracks, playlist]);

  const handleEnded = useCallback(() => {
    const next = currentIndexRef.current + 1;
    if (next < tracks.length) {
      currentIndexRef.current = next;
      setCurrentIndex(next);
    } else if (playlist?.loop_enabled) {
      currentIndexRef.current = 0;
      setCurrentIndex(0);
    }
    // sem loop e acabou: para
  }, [tracks, playlist]);

  // Toca a faixa atual quando index muda
  useEffect(() => {
    if (!audioRef.current || !tracks.length || !playlist) return;

    const track = tracks[currentIndex];
    if (!track?.file_url) return;

    const audio = audioRef.current;
    audio.removeEventListener("ended", handleEnded);
    audio.removeEventListener("error", handleError);

    audio.src = assetUrl(track.file_url);
    const trackVolume = playlist.track_volumes?.[track.id];
    audio.volume = trackVolume ?? playlist.volume_default ?? 0.7;

    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    audio.play().catch(() => {
      // autoplay bloqueado — aguarda interação do usuário
    });

    onStatusChange?.({ playing: true, track, index: currentIndex });
  }, [currentIndex, tracks, playlist]);

  // Componente invisível — só lógica
  return null;
}
