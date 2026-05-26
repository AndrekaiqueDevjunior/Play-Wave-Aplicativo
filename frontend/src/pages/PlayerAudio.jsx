/**
 * Página de Player Áudio
 *
 * Demonstra integração completa:
 * - AudioManager central
 * - AudioControlPanel UI
 * - Playback events logging
 * - Resolução de agenda (folder schedules)
 * - Resolução de spots
 */

import React, { useEffect, useRef, useState } from "react";
import { useAudioManager } from "@/hooks/useAudioManager";
import AudioControlPanel from "@/components/audio/AudioControlPanel";
import { logTrackStarted, logTrackEnded, logSpotStarted } from "@/lib/playbackEventLogger";
import { AUDIO_STATE, AUDIO_MODE } from "@/lib/audioManager";
import { Loader2, AlertCircle } from "lucide-react";
import {
  resolveActiveFolderForNow,
  resolveActiveSpotsForNow,
  shouldPlaySpotNow,
  hasFolderChanged,
  createPlaybackQueue,
} from "@/utils/audioScheduleResolver";

/**
 * Exemplo de uso em um player ou aplicação que reproduz rádio
 */
export default function PlayerAudio() {
  const deviceId = "device-123"; // Seria obtido do store/auth
  const playlistId = "playlist-456"; // Seria obtido de params

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [playlist, setPlaylist] = useState(null);
  const [currentFolder, setCurrentFolder] = useState(null);
  const [spotTimers, setSpotTimers] = useState(new Map());

  // Refs dos players
  const radioRef = useRef(null);
  const mediaRef = useRef(null);
  const spotRef = useRef(null);

  // AudioManager
  const { initPlayers, loadRadioPlaylist, playRadio, playSpot, silence, state } =
    useAudioManager({
      fadeMs: 200,
    });

  // Initialize
  useEffect(() => {
    const initAudio = async () => {
      try {
        setLoading(true);

        // 1. Buscar playlist + agendamentos
        // const response = await fetch(`/audio/playlists/${playlistId}`);
        // const data = await response.json();
        // setPlaylist(data);

        // Mock para exemplo
        const mockPlaylist = {
          id: playlistId,
          items: [
            {
              id: "track-1",
              name: "Música 1",
              file_url: "/audio/track1.mp3",
              duration_seconds: 180,
            },
            {
              id: "track-2",
              name: "Música 2",
              file_url: "/audio/track2.mp3",
              duration_seconds: 240,
            },
            {
              id: "track-3",
              name: "Música 3",
              file_url: "/audio/track3.mp3",
              duration_seconds: 200,
            },
          ],
          folder_schedules: [
            {
              id: "sched-1",
              folder_id: "folder-1",
              start_time: "06:00",
              end_time: "12:00",
              play_mode: "sequential",
              priority: 1,
            },
            {
              id: "sched-2",
              folder_id: "folder-2",
              start_time: "12:00",
              end_time: "18:00",
              play_mode: "shuffle",
              priority: 1,
            },
          ],
          spot_schedules: [
            {
              id: "spot-sched-1",
              spot_id: "spot-1",
              interval_seconds: 1800,
              start_time: "06:00",
              end_time: "22:00",
              priority: 5,
            },
          ],
        };

        setPlaylist(mockPlaylist);

        // 2. Inicializar players (HTML audio elements)
        if (radioRef.current && mediaRef.current && spotRef.current) {
          initPlayers(radioRef.current, mediaRef.current, spotRef.current);

          // 3. Carregar playlist rádio
          if (mockPlaylist.items) {
            // Usar modo shuffle_enabled da playlist se configurado
            const mode = mockPlaylist.shuffle_enabled 
              ? AUDIO_MODE.SHUFFLE 
              : AUDIO_MODE.SEQUENTIAL;
            
            const queue = createPlaybackQueue(mockPlaylist.items, mode);
            loadRadioPlaylist(queue, mode);

            // 4. Iniciar reprodução
            await playRadio();
          }
        }

        setError(null);
      } catch (err) {
        console.error("Error initializing player:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    initAudio();
  }, [playlistId, initPlayers, loadRadioPlaylist, playRadio]);

  // Log events
  useEffect(() => {
    if (state.current === AUDIO_STATE.RADIO && playlist?.items) {
      // Encontrar track atual
      const currentTrack = playlist.items[0]; // Simplificado

      // Log quando começa
      if (state.isPlaying && currentTrack) {
        logTrackStarted(deviceId, currentTrack.id, playlistId).catch(
          console.error
        );
      }
    }

    if (state.current === AUDIO_STATE.SPOT && playlist?.spot_schedules) {
      const currentSpot = playlist.spot_schedules[0]; // Simplificado
      if (currentSpot) {
        logSpotStarted(deviceId, currentSpot.spot_id, playlistId).catch(
          console.error
        );
      }
    }
  }, [state.current, state.isPlaying, deviceId, playlistId, playlist]);

  // Resolver de agenda - troca pasta automaticamente conforme horário
  useEffect(() => {
    if (!playlist?.folder_schedules || playlist.folder_schedules.length === 0) {
      return;
    }

    const checkSchedule = () => {
      const activeFolder = resolveActiveFolderForNow(playlist.folder_schedules);
      
      if (hasFolderChanged(currentFolder, activeFolder)) {
        console.log('[player-audio] Mudança de pasta detectada:', {
          previous: currentFolder?.name || 'nenhuma',
          current: activeFolder?.name || 'nenhuma',
          time: new Date().toLocaleTimeString(),
        });
        
        setCurrentFolder(activeFolder);
        
        // Carregar faixas da nova pasta
        if (activeFolder?.tracks && activeFolder.tracks.length > 0) {
          const mode = activeFolder.play_mode || AUDIO_MODE.SEQUENTIAL;
          const queue = createPlaybackQueue(activeFolder.tracks, mode);
          
          console.log('[player-audio] Carregando faixas da pasta:', {
            folder: activeFolder.name,
            mode,
            trackCount: queue.length,
          });
          
          loadRadioPlaylist(queue, mode);
          playRadio();
        } else if (!activeFolder) {
          // Nenhuma pasta ativa no horário atual
          console.log('[player-audio] Nenhuma pasta ativa no horário atual');
          silence();
        }
      }
    };

    // Verificar imediatamente
    checkSchedule();
    
    // Verificar a cada minuto
    const interval = setInterval(checkSchedule, 60000);

    return () => clearInterval(interval);
  }, [playlist, currentFolder, loadRadioPlaylist, playRadio, silence]);

  // Resolver de spots - toca spots no intervalo configurado
  useEffect(() => {
    if (!playlist?.spot_schedules || playlist.spot_schedules.length === 0) {
      return;
    }

    const checkSpots = async () => {
      const activeSpots = resolveActiveSpotsForNow(playlist.spot_schedules);
      
      if (activeSpots.length === 0) {
        return;
      }

      for (const spotSchedule of activeSpots) {
        const lastPlayed = spotTimers.get(spotSchedule.id);
        
        if (shouldPlaySpotNow(spotSchedule, lastPlayed)) {
          console.log('[player-audio] Tocando spot:', {
            spot: spotSchedule.spot?.name || spotSchedule.spot_id,
            interval: spotSchedule.interval_seconds,
            lastPlayed: lastPlayed?.toLocaleTimeString() || 'nunca',
            now: new Date().toLocaleTimeString(),
          });
          
          try {
            // Buscar track do spot
            const spotTrack = spotSchedule.spot?.track || spotSchedule.track;
            
            if (spotTrack?.file_url) {
              const policy = spotSchedule.spot?.insertion_policy || 'INTERRUPT';
              await playSpot(spotTrack.file_url, policy);
              
              // Registrar log de reprodução
              await logSpotStarted(
                deviceId,
                spotSchedule.spot_id,
                playlistId
              ).catch(console.error);
              
              // Atualizar timer
              setSpotTimers(prev => {
                const newTimers = new Map(prev);
                newTimers.set(spotSchedule.id, new Date());
                return newTimers;
              });
            } else {
              console.warn('[player-audio] Spot sem track:', spotSchedule.id);
            }
          } catch (err) {
            console.error('[player-audio] Erro ao tocar spot:', err);
          }
        }
      }
    };

    // Verificar imediatamente
    checkSpots();
    
    // Verificar a cada 30 segundos
    const interval = setInterval(checkSpots, 30000);

    return () => clearInterval(interval);
  }, [playlist, spotTimers, playSpot, deviceId, playlistId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="flex gap-2 text-red-600">
          <AlertCircle className="h-6 w-6" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Rádio Indoor</h1>
        <p className="text-gray-600">Reprodutor de áudio com agendamento</p>
      </div>

      {/* Hidden audio elements */}
      <audio
        ref={radioRef}
        crossOrigin="anonymous"
        onError={(e) => console.error("Radio error:", e)}
      />
      <audio
        ref={mediaRef}
        crossOrigin="anonymous"
        onError={(e) => console.error("Media error:", e)}
      />
      <audio
        ref={spotRef}
        crossOrigin="anonymous"
        onError={(e) => console.error("Spot error:", e)}
      />

      {/* Control panel */}
      <AudioControlPanel />

      {/* Playlist info */}
      {playlist && (
        <div className="border rounded-lg p-4 space-y-2">
          <h2 className="font-semibold">Fila de Reprodução</h2>
          <p className="text-sm text-gray-600">
            {playlist.items?.length || 0} faixa
            {playlist.items?.length !== 1 ? "s" : ""}
          </p>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {playlist.items?.map((track, idx) => (
              <div
                key={track.id}
                className="text-sm p-2 bg-gray-50 rounded flex justify-between"
              >
                <span>{idx + 1}. {track.name}</span>
                <span className="text-gray-500 text-xs">
                  {Math.floor(track.duration_seconds / 60)}:
                  {(track.duration_seconds % 60).toString().padStart(2, "0")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status */}
      <div className="border rounded-lg p-4 text-sm space-y-2">
        <div>
          <span className="font-medium">Estado:</span>{" "}
          <span className="text-gray-600">
            {state.current === AUDIO_STATE.SILENT && "Silêncio"}
            {state.current === AUDIO_STATE.RADIO && "Rádio"}
            {state.current === AUDIO_STATE.MEDIA_AUDIO && "Vídeo"}
            {state.current === AUDIO_STATE.SPOT && "Spot"}
          </span>
        </div>
        <div>
          <span className="font-medium">Reproduzindo:</span>{" "}
          <span className="text-gray-600">{state.isPlaying ? "Sim" : "Não"}</span>
        </div>
        <div>
          <span className="font-medium">Volume:</span>{" "}
          <span className="text-gray-600">{Math.round(state.volume * 100)}%</span>
        </div>
        <div>
          <span className="font-medium">Modo:</span>{" "}
          <span className="text-gray-600">
            {state.radioMode === AUDIO_MODE.SEQUENTIAL && "Sequencial"}
            {state.radioMode === AUDIO_MODE.SHUFFLE && "Embaralhado"}
            {state.radioMode === AUDIO_MODE.LOOP && "Loop"}
          </span>
        </div>
      </div>
    </div>
  );
}
