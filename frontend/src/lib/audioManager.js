/**
 * Audio Manager — Controle central de reprodução de áudio
 *
 * Responsabilidades:
 * - Gerenciar múltiplos players (rádio, vídeo, spots)
 * - Priorização automática (spot > vídeo > rádio > silêncio)
 * - Fade in/out suave entre fontes
 * - Fila sequencial + shuffle
 * - Evitar sobreposição de áudio
 * - Registrar eventos de reprodução
 */

export const AUDIO_STATE = {
  RADIO: "radio",           // Rádio (ambiente)
  MEDIA_AUDIO: "media_audio", // Áudio de vídeo/mídia
  SPOT: "spot",             // Anúncio/jingle
  SILENT: "silent",         // Silêncio
};

export const AUDIO_MODE = {
  SEQUENTIAL: "sequential",
  SHUFFLE: "shuffle",
  LOOP: "loop",
};

/**
 * Gerencia o estado de reprodução de áudio.
 * Usa um listener para notificar mudanças.
 */
export class AudioManager {
  constructor(options = {}) {
    this.state = {
      current: AUDIO_STATE.SILENT,
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      volume: 1.0,
      fadeMs: options.fadeMs || 200,
      currentTrack: null,
    };

    this.players = {
      radio: null,          // HTMLAudioElement ou Web Audio
      mediaAudio: null,
      spot: null,
    };

    this.queue = {
      radio: [],            // Lista de faixas rádio
      radioIndex: 0,
      radioMode: AUDIO_MODE.SEQUENTIAL,
      spot: null,           // Próximo spot
      spotTime: null,       // Quando tocar
    };

    this.listeners = [];
    this.fadeTimer = null;
  }

  /**
   * Registra listener para mudanças de estado
   */
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Notifica todos os listeners
   */
  _notify(patch = {}) {
    this.state = { ...this.state, ...patch };
    this.listeners.forEach(listener => listener(this.state));
  }

  /**
   * Inicializa players
   */
  initPlayers(radioElement, mediaElement, spotElement) {
    this.players.radio = radioElement;
    this.players.mediaAudio = mediaElement;
    this.players.spot = spotElement;

    // Setup event listeners
    if (this.players.radio) {
      this.players.radio.addEventListener('timeupdate', () => this._onTimeUpdate('radio'));
      this.players.radio.addEventListener('ended', () => this._onTrackEnded('radio'));
      this.players.radio.addEventListener('error', () => this._onTrackError('radio'));
    }

    if (this.players.mediaAudio) {
      this.players.mediaAudio.addEventListener('timeupdate', () => this._onTimeUpdate('media'));
      this.players.mediaAudio.addEventListener('ended', () => this._onTrackEnded('media'));
    }

    // Spot ended is handled by the per-play _spotEndedHandler registered in playSpot()

  }

  /**
   * Carrega playlist rádio
   */
  loadRadioPlaylist(tracks, mode = AUDIO_MODE.SEQUENTIAL) {
    this.queue.radio = tracks || [];
    this.queue.radioIndex = 0;
    this.queue.radioMode = mode;

    if (mode === AUDIO_MODE.SHUFFLE) {
      this._shuffleQueue();
    }

    this._notify({ radioQueue: this.queue.radio, radioMode: mode });
  }

  /**
   * Embaralha fila (Fisher-Yates)
   */
  _shuffleQueue() {
    const queue = [...this.queue.radio];
    for (let i = queue.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [queue[i], queue[j]] = [queue[j], queue[i]];
    }
    this.queue.radio = queue;
  }

  /**
   * Reproduz rádio (faixa atual ou próxima)
   */
  async playRadio(trackUrl = null) {
    if (!this.players.radio) return;

    // Já tocando rádio e não foi pedida faixa específica: não reinicia
    if (!trackUrl && this.state.current === AUDIO_STATE.RADIO && this.state.isPlaying) return;

    let track = null;
    if (!trackUrl) {
      if (this.queue.radioIndex >= this.queue.radio.length) {
        this.queue.radioIndex = 0;
        if (this.queue.radioMode === AUDIO_MODE.SHUFFLE) {
          this._shuffleQueue();
        }
      }
      if (this.queue.radio.length === 0) return;
      track = this.queue.radio[this.queue.radioIndex];
      trackUrl = track.file_url;
    }

    // Fade out + load novo
    await this._fadeOut(this.players.radio, this.state.fadeMs);
    this.players.radio.src = trackUrl;
    await this._fadeIn(this.players.radio, this.state.fadeMs);

    this._notify({ current: AUDIO_STATE.RADIO, isPlaying: true, currentTrack: track });
  }

  /**
   * Reproduz áudio de vídeo/mídia
   */
  async playMediaAudio(mediaElement) {
    if (!this.players.mediaAudio) return;

    // Se há spot em fila, aguarda ele terminar
    if (this.state.current === AUDIO_STATE.SPOT) {
      return; // Aguarda spot terminar
    }

    // Fade rádio
    if (this.state.current === AUDIO_STATE.RADIO) {
      await this._fadeOut(this.players.radio, this.state.fadeMs);
    }

    // Fade in vídeo
    this.players.mediaAudio.srcObject = mediaElement.srcObject || mediaElement;
    await this._fadeIn(this.players.mediaAudio, this.state.fadeMs);

    this._notify({ current: AUDIO_STATE.MEDIA_AUDIO, isPlaying: true });
  }

  /**
   * Reproduz spot (anúncio)
   * Pausa rádio/vídeo, toca spot, retoma
   */
  async playSpot(spotUrl, insertionPolicy = 'wait_silence') {
    if (!this.players.spot) return;

    // BUG D3 FIX: captura o estado ANTES de entrar em SPOT.
    // Se já estamos em SPOT (travado), usa RADIO como fallback para não tentar
    // retomar um spot como se fosse a fonte de fundo.
    const previous = this.state.current === AUDIO_STATE.SPOT
      ? (this.players.radio?.src ? AUDIO_STATE.RADIO : AUDIO_STATE.SILENT)
      : this.state.current;

    // Cancela listener anterior para evitar retomadas duplicadas
    if (this._spotEndedHandler) {
      this.players.spot.removeEventListener("ended", this._spotEndedHandler);
      this._spotEndedHandler = null;
    }

    // Política de inserção
    if (insertionPolicy === 'interrupt') {
      await this._fadeOut(
        previous === AUDIO_STATE.RADIO ? this.players.radio : this.players.mediaAudio,
        this.state.fadeMs
      );
    } else if (insertionPolicy === 'wait_silence') {
      // Aguarda pausa natural (não implementado aqui)
    } else if (insertionPolicy === 'fade_mix') {
      const player = previous === AUDIO_STATE.RADIO ? this.players.radio : this.players.mediaAudio;
      if (player) player.volume = 0.3;
    }

    // BUG D3 FIX: registra listener `ended` para retomar o rádio automaticamente.
    // { once: true } garante que o handler é removido após disparar uma vez.
    this._spotEndedHandler = () => {
      this._spotEndedHandler = null;
      this._resumeAfterSpot(previous).catch(() => {});
    };
    this.players.spot.addEventListener("ended", this._spotEndedHandler, { once: true });

    // Toca spot
    this.players.spot.src = spotUrl;
    await this._fadeIn(this.players.spot, 100);

    this._notify({ current: AUDIO_STATE.SPOT, isPlaying: true });
  }

  /**
   * Quando spot termina, retoma anterior
   */
  async _resumeAfterSpot(previous) {
    if (!this.players.spot) return;

    await this._fadeOut(this.players.spot, 100);

    const player = previous === AUDIO_STATE.RADIO
      ? this.players.radio
      : this.players.mediaAudio;

    if (player) {
      if (previous === AUDIO_STATE.RADIO) {
        player.volume = 1.0; // Retoma volume
      }
      await this._fadeIn(player, this.state.fadeMs);
    }

    this._notify({ current: previous, isPlaying: true });
  }

  /**
   * Silencia tudo
   */
  async silence() {
    await this._fadeOut(this.players.radio, this.state.fadeMs);
    await this._fadeOut(this.players.mediaAudio, this.state.fadeMs);
    await this._fadeOut(this.players.spot, this.state.fadeMs);

    this._notify({ current: AUDIO_STATE.SILENT, isPlaying: false, currentTrack: null });
  }

  /**
   * Pausa o que está tocando
   */
  pause() {
    const player = this._getCurrentPlayer();
    if (player) player.pause();
    this._notify({ isPlaying: false });
  }

  /**
   * Retoma o que estava tocando
   */
  resume() {
    const player = this._getCurrentPlayer();
    if (player) player.play();
    this._notify({ isPlaying: true });
  }

  /**
   * Obtém volume (0-1)
   */
  getVolume() {
    return this.state.volume;
  }

  /**
   * Define volume global
   */
  setVolume(volume) {
    const v = Math.max(0, Math.min(1, volume));
    this.state.volume = v;

    // Aplica a todos os players
    if (this.players.radio) this.players.radio.volume = v;
    if (this.players.mediaAudio) this.players.mediaAudio.volume = v;
    if (this.players.spot) this.players.spot.volume = v;

    this._notify({ volume: v });
  }

  /**
   * Próxima faixa rádio
   */
  nextTrack() {
    this.queue.radioIndex++;
    if (this.queue.radioIndex >= this.queue.radio.length) {
      this.queue.radioIndex = 0;
    }
    this._playRadioByIndex();
  }

  /**
   * Faixa anterior rádio
   */
  previousTrack() {
    this.queue.radioIndex--;
    if (this.queue.radioIndex < 0) {
      this.queue.radioIndex = this.queue.radio.length - 1;
    }
    this._playRadioByIndex();
  }

  /**
   * Toca faixa pelo índice atual (sem guard de "já tocando")
   */
  async _playRadioByIndex() {
    if (!this.players.radio || this.queue.radio.length === 0) return;
    const track = this.queue.radio[this.queue.radioIndex];
    if (!track?.file_url) return;
    await this._fadeOut(this.players.radio, this.state.fadeMs);
    this.players.radio.src = track.file_url;
    await this._fadeIn(this.players.radio, this.state.fadeMs);
    this._notify({ current: AUDIO_STATE.RADIO, isPlaying: true, currentTrack: track });
  }

  /**
   * Muda modo de fila
   */
  setRadioMode(mode) {
    this.queue.radioMode = mode;
    if (mode === AUDIO_MODE.SHUFFLE) {
      this._shuffleQueue();
    }
    this._notify({ radioMode: mode });
  }

  /**
   * Fade in suave
   */
  _fadeIn(element, duration = 200) {
    return new Promise(resolve => {
      if (!element) {
        resolve();
        return;
      }

      element.volume = 0;
      element.play().catch(() => {}); // Toca mesmo se falhar

      const startTime = Date.now();
      const step = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        element.volume = progress * this.state.volume;

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          element.volume = this.state.volume;
          resolve();
        }
      };

      requestAnimationFrame(step);
    });
  }

  /**
   * Fade out suave
   */
  _fadeOut(element, duration = 200) {
    return new Promise(resolve => {
      if (!element) {
        resolve();
        return;
      }

      const startTime = Date.now();
      const startVolume = element.volume;
      const step = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        element.volume = startVolume * (1 - progress);

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          element.volume = 0;
          element.pause();
          resolve();
        }
      };

      requestAnimationFrame(step);
    });
  }

  /**
   * Callbacks internos
   */
  _onTimeUpdate(source) {
    if (source === 'radio' && this.players.radio) {
      this._notify({
        currentTime: this.players.radio.currentTime,
        duration: this.players.radio.duration,
      });
    }
  }

  _onTrackEnded(source) {
    if (source === 'radio') {
      this.nextTrack();
    }
  }

  _onTrackError(source) {
    if (source === 'radio') {
      console.warn('[AudioManager] track error, skipping to next');
      this.nextTrack();
    }
  }

  _getCurrentPlayer() {
    switch (this.state.current) {
      case AUDIO_STATE.RADIO:
        return this.players.radio;
      case AUDIO_STATE.MEDIA_AUDIO:
        return this.players.mediaAudio;
      case AUDIO_STATE.SPOT:
        return this.players.spot;
      default:
        return null;
    }
  }

  /**
   * Destruir manager
   */
  destroy() {
    if (this._spotEndedHandler && this.players.spot) {
      this.players.spot.removeEventListener("ended", this._spotEndedHandler);
      this._spotEndedHandler = null;
    }
    this.listeners = [];
    this.silence();
  }
}

// Export singleton
let instance = null;

export function createAudioManager(options) {
  if (!instance) {
    instance = new AudioManager(options);
  }
  return instance;
}

export function getAudioManager() {
  if (!instance) {
    instance = new AudioManager();
  }
  return instance;
}
