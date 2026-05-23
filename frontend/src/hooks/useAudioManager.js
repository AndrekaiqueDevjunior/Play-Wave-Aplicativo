import { useEffect, useRef, useState, useCallback } from "react";
import { createAudioManager, getAudioManager, AUDIO_STATE, AUDIO_MODE } from "@/lib/audioManager";

/**
 * Hook para usar AudioManager em componentes
 *
 * Exemplo:
 * const { play, pause, volume, setVolume } = useAudioManager();
 * const radio = useRef(null);
 * const media = useRef(null);
 *
 * useEffect(() => {
 *   manager.initPlayers(radio.current, media.current, spot.current);
 * }, [manager]);
 */
export function useAudioManager(options = {}) {
  const managerRef = useRef(null);
  const [state, setState] = useState({
    current: AUDIO_STATE.SILENT,
    isPlaying: false,
    currentTime: 0,
    duration: 0,
    volume: 1.0,
    radioMode: AUDIO_MODE.SEQUENTIAL,
    radioQueue: [],
  });

  // Inicializa manager na primeira renderização
  useEffect(() => {
    if (!managerRef.current) {
      managerRef.current = createAudioManager(options);

      // Subscribe para mudanças de estado
      const unsubscribe = managerRef.current.subscribe((newState) => {
        setState((prev) => ({ ...prev, ...newState }));
      });

      return () => {
        unsubscribe();
      };
    }
  }, [options]);

  // Callbacks
  const playRadio = useCallback((trackUrl) => {
    managerRef.current?.playRadio(trackUrl);
  }, []);

  const playMediaAudio = useCallback((mediaElement) => {
    managerRef.current?.playMediaAudio(mediaElement);
  }, []);

  const playSpot = useCallback((spotUrl, policy) => {
    managerRef.current?.playSpot(spotUrl, policy);
  }, []);

  const silence = useCallback(() => {
    managerRef.current?.silence();
  }, []);

  const pause = useCallback(() => {
    managerRef.current?.pause();
  }, []);

  const resume = useCallback(() => {
    managerRef.current?.resume();
  }, []);

  const setVolume = useCallback((volume) => {
    managerRef.current?.setVolume(volume);
  }, []);

  const nextTrack = useCallback(() => {
    managerRef.current?.nextTrack();
  }, []);

  const previousTrack = useCallback(() => {
    managerRef.current?.previousTrack();
  }, []);

  const setRadioMode = useCallback((mode) => {
    managerRef.current?.setRadioMode(mode);
  }, []);

  const loadRadioPlaylist = useCallback((tracks, mode) => {
    managerRef.current?.loadRadioPlaylist(tracks, mode);
  }, []);

  const initPlayers = useCallback((radioElement, mediaElement, spotElement) => {
    managerRef.current?.initPlayers(radioElement, mediaElement, spotElement);
  }, []);

  return {
    // Estado
    state,
    current: state.current,
    isPlaying: state.isPlaying,
    volume: state.volume,
    radioMode: state.radioMode,
    currentTime: state.currentTime,
    duration: state.duration,

    // Métodos
    playRadio,
    playMediaAudio,
    playSpot,
    silence,
    pause,
    resume,
    setVolume,
    nextTrack,
    previousTrack,
    setRadioMode,
    loadRadioPlaylist,
    initPlayers,

    // Manager direto (para chamadas avançadas)
    manager: managerRef.current,
  };
}

/**
 * Hook simples para estado do player
 */
export function useAudioState() {
  const manager = getAudioManager();
  const [state, setState] = useState({
    current: AUDIO_STATE.SILENT,
    isPlaying: false,
    volume: 1.0,
  });

  useEffect(() => {
    const unsubscribe = manager.subscribe((newState) => {
      setState((prev) => ({ ...prev, ...newState }));
    });

    return unsubscribe;
  }, [manager]);

  return state;
}

/**
 * Hook para controlar volume com slider
 */
export function useAudioVolume() {
  const manager = getAudioManager();
  const [volume, setVolumeState] = useState(manager.getVolume());

  const setVolume = useCallback((v) => {
    manager.setVolume(v);
    setVolumeState(v);
  }, [manager]);

  return { volume, setVolume };
}
