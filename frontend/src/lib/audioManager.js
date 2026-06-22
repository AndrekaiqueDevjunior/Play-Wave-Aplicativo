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

// Watchdog de reprodução: play() pode ficar pendurado (nunca resolve nem
// rejeita) em alguns navegadores/cenários de rede — sem um limite, o spot ou
// a faixa de rádio ficam "presos mudos" para sempre. 10s é generoso o
// suficiente para não cortar uma faixa que só demora a iniciar.
const PLAY_WATCHDOG_TIMEOUT_MS = 10_000;

// Quarentena: um áudio que falhou não é tentado de novo por um tempo, mas
// expira sozinho — assim um arquivo corrigido no servidor volta a tocar sem
// precisar reiniciar o player.
const FAILED_AUDIO_TTL_MS = 5 * 60 * 1000;

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
      autoplayBlocked: false,
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

    // Spot represado pela política WAIT_SILENCE: guarda { spotUrl, insertionPolicy,
    // spotItem } enquanto espera o evento 'ended' da faixa de rádio atual.
    // null quando não há spot pendente.
    this._pendingSpot = null;

    // audioId -> timestamp da falha (quarentena com TTL, ver _isAudioMarkedFailed)
    this.failedAudioIds = new Map();
    // Conta pulos consecutivos de faixas de rádio sem sucesso — limita a
    // tentativas <= tamanho da fila para nunca girar em loop infinito.
    this._radioSkipStreak = 0;
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

      if (track?.id && this._isAudioMarkedFailed(track.id)) {
        this._handleRadioTrackFailure(track, "quarantine_ttl", { markFailed: false });
        return;
      }
    }

    // Fade out + load novo
    await this._fadeOut(this.players.radio, this.state.fadeMs);
    this.players.radio.src = trackUrl;
    const result = await this._fadeIn(this.players.radio, this.state.fadeMs, true, track, "radio");

    if (track && !result.ok && result.reason !== "autoplay_blocked") {
      this._handleRadioTrackFailure(track, result.reason);
      return;
    }

    this._radioSkipStreak = 0;
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
    await this._fadeIn(this.players.mediaAudio, this.state.fadeMs, true, null, "media_audio");

    this._notify({ current: AUDIO_STATE.MEDIA_AUDIO, isPlaying: true });
  }

  /**
   * Reproduz spot (anúncio)
   * Pausa rádio/vídeo, toca spot, retoma
   */
  /**
   * Retorna true se um spot está tocando agora.
   * Usado pelo Player para evitar disparar outro spot enquanto este não terminou.
   */
  isSpotPlaying() {
    return (
      this.state.current === AUDIO_STATE.SPOT &&
      this.players.spot &&
      !this.players.spot.paused &&
      !this.players.spot.ended
    );
  }

  /**
   * Retorna true se há música/vídeo de fundo audível tocando agora (não pausado,
   * não terminado). Usado pela política WAIT_SILENCE para decidir entre tocar o
   * spot imediatamente (fundo já em silêncio) ou represá-lo até o 'ended'.
   */
  _isBackgroundActivelyPlaying(bgPlayer) {
    return !!(bgPlayer && bgPlayer.src && !bgPlayer.paused && !bgPlayer.ended);
  }

  async playSpot(spotUrl, insertionPolicy = 'wait_silence', spotItem = null) {
    if (!this.players.spot) return;

    // Não sobrepõe spot sobre spot — aguarda o atual terminar
    if (this.isSpotPlaying()) return;

    const spotId = spotItem?.id || spotItem?.spot_id || null;
    if (spotId && this._isAudioMarkedFailed(spotId)) {
      this._logAudio("SKIP_FAILED_AUDIO", {
        label: "spot",
        audioId: spotId,
        url: spotUrl,
        reason: "quarantine_ttl",
      });
      return;
    }

    // Captura o estado ANTES de entrar em SPOT.
    // Se já estamos em SPOT (fallback improvável), usa RADIO.
    const previous = this.state.current === AUDIO_STATE.SPOT
      ? (this.players.radio?.src ? AUDIO_STATE.RADIO : AUDIO_STATE.SILENT)
      : this.state.current;

    const bgPlayer = previous === AUDIO_STATE.RADIO ? this.players.radio : this.players.mediaAudio;

    // WAIT_SILENCE (= WAIT_TRACK_END do SPEC-006): nunca toca o spot por cima
    // da música. Se o fundo está audível agora, represa o spot e só o toca
    // quando a faixa de rádio atual terminar (ver _onTrackEnded → 'ended').
    if (insertionPolicy === 'wait_silence' && this._isBackgroundActivelyPlaying(bgPlayer)) {
      this._pendingSpot = { spotUrl, insertionPolicy, spotItem };
      this._logAudio("SPOT_QUEUED", {
        label: "spot",
        audioId: spotId,
        url: spotUrl,
        reason: "wait_track_end",
      });
      return;
    }

    // Cancela listener anterior para evitar retomadas duplicadas
    if (this._spotEndedHandler) {
      this.players.spot.removeEventListener("ended", this._spotEndedHandler);
      this._spotEndedHandler = null;
    }

    // Política de inserção
    if (insertionPolicy === 'interrupt') {
      await this._fadeOut(bgPlayer, this.state.fadeMs);
    } else if (insertionPolicy === 'wait_silence') {
      // Fundo já estava parado/em silêncio (ver checagem acima) — apenas
      // garante volume zerado antes do spot, sem esperar fade longo.
      if (bgPlayer) await this._fadeOut(bgPlayer, this.state.fadeMs);
    } else if (insertionPolicy === 'fade_mix') {
      // Mantém fundo em volume reduzido durante o spot
      if (bgPlayer) bgPlayer.volume = 0.25;
    }

    // Handler de fim: retoma rádio quando spot termina
    this._spotEndedHandler = () => {
      this._spotEndedHandler = null;
      this._resumeAfterSpot(previous).catch(() => {});
    };
    this.players.spot.addEventListener("ended", this._spotEndedHandler, { once: true });

    // Handler de erro: se o áudio falhar (URL inválida, rede, etc.)
    // retoma imediatamente sem travar o player no estado SPOT
    const errorHandler = () => {
      console.warn("[AudioManager] spot falhou ao carregar:", spotUrl);
      if (spotId) this._markAudioFailed(spotId);
      this._logAudio("SKIP_FAILED_AUDIO", {
        label: "spot",
        audioId: spotId,
        url: spotUrl,
        reason: "media_error_event",
      });
      if (this._spotEndedHandler) {
        this.players.spot.removeEventListener("ended", this._spotEndedHandler);
        this._spotEndedHandler = null;
      }
      this._resumeAfterSpot(previous).catch(() => {});
    };
    this.players.spot.addEventListener("error", errorHandler, { once: true });

    // Limpa o handler de erro assim que o spot começar a tocar com sucesso
    this.players.spot.addEventListener("playing", () => {
      this.players.spot.removeEventListener("error", errorHandler);
    }, { once: true });

    // Toca spot — load() garante que o src é processado antes do play
    this.players.spot.src = spotUrl;
    this.players.spot.load();
    // useMutedTrick=false: o rádio já está tocando audível neste ponto,
    // então o navegador já liberou áudio na página — tocar o spot mudo
    // arriscaria perder o clipe inteiro (spots costumam ser curtos).
    const result = await this._fadeIn(this.players.spot, 100, false, spotItem, "spot");

    if (!result.ok && result.reason !== "autoplay_blocked") {
      // play() travou (watchdog) ou foi rejeitado por motivo diferente de
      // bloqueio de autoplay — não fica preso em SPOT: limpa os handlers
      // pendentes e retoma a fonte anterior normalmente.
      this.players.spot.removeEventListener("error", errorHandler);
      if (this._spotEndedHandler) {
        this.players.spot.removeEventListener("ended", this._spotEndedHandler);
        this._spotEndedHandler = null;
      }
      this._logAudio("SKIP_FAILED_AUDIO", {
        label: "spot",
        audioId: spotId,
        url: spotUrl,
        reason: result.reason,
      });
      await this._resumeAfterSpot(previous);
      return;
    }

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
        const track = this.queue.radio[this.queue.radioIndex] || this.state.currentTrack;
        const result = await this._fadeIn(player, this.state.fadeMs, true, track, "radio");
        if (track && !result.ok && result.reason !== "autoplay_blocked") {
          this._handleRadioTrackFailure(track, result.reason);
          return;
        }
        this._radioSkipStreak = 0;
      } else {
        await this._fadeIn(player, this.state.fadeMs, true, null, "media_audio");
      }
    }

    this._notify({ current: previous, isPlaying: true });
  }

  /**
   * Silencia tudo
   */
  async silence() {
    this._pendingSpot = null;
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
   * Chamado quando o usuário clica para desbloquear autoplay.
   * Retenta o play() em todos os elementos suspensos.
   */
  async unlockAutoplay() {
    this._notify({ autoplayBlocked: false });
    const current = this._getCurrentPlayer();
    if (current && current.paused && current.src) {
      current.muted = false;
      await current.play().catch(() => {});
    }
    if (this.players.radio?.paused && this.players.radio?.src) {
      this.players.radio.muted = false;
      await this.players.radio.play().catch(() => {});
    }
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

    if (track?.id && this._isAudioMarkedFailed(track.id)) {
      this._handleRadioTrackFailure(track, "quarantine_ttl", { markFailed: false });
      return;
    }

    await this._fadeOut(this.players.radio, this.state.fadeMs);
    this.players.radio.src = track.file_url;
    const result = await this._fadeIn(this.players.radio, this.state.fadeMs, true, track, "radio");

    if (!result.ok && result.reason !== "autoplay_blocked") {
      this._handleRadioTrackFailure(track, result.reason);
      return;
    }

    this._radioSkipStreak = 0;
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
   * Log estruturado dos eventos do watchdog de áudio.
   * Mantém um formato único { event, ...payload, ts } para facilitar
   * filtragem/parsing posterior (ex.: ferramentas de observabilidade).
   */
  _logAudio(event, payload = {}) {
    const entry = { event, ...payload, ts: new Date().toISOString() };
    const isWarning = [
      "PLAY_TIMEOUT",
      "PLAY_REJECTED",
      "SKIP_FAILED_AUDIO",
      "NO_VALID_AUDIO",
    ].includes(event);
    if (isWarning) {
      console.warn(`[AudioManager] ${event}`, entry);
    } else {
      console.log(`[AudioManager] ${event}`, entry);
    }
  }

  /**
   * Verifica se um audioId está em quarentena (falhou recentemente).
   * TTL é checado de forma preguiçosa — sem timer de fundo: se já expirou,
   * remove a entrada e libera o áudio para nova tentativa.
   */
  _isAudioMarkedFailed(audioId) {
    if (!audioId) return false;
    const failedAt = this.failedAudioIds.get(audioId);
    if (failedAt === undefined) return false;
    if (Date.now() - failedAt > FAILED_AUDIO_TTL_MS) {
      this.failedAudioIds.delete(audioId);
      return false;
    }
    return true;
  }

  /**
   * Marca um audioId como falho — entra em quarentena por FAILED_AUDIO_TTL_MS.
   */
  _markAudioFailed(audioId) {
    if (!audioId) return;
    this.failedAudioIds.set(audioId, Date.now());
  }

  /**
   * Watchdog de play(): corre element.play() contra um timeout.
   *
   * Problema que resolve: em alguns navegadores/cenários de rede, a Promise
   * de audio.play() nunca resolve nem rejeita — o áudio fica "preso mudo"
   * para sempre, sem nenhum sinal de erro. Promise.race garante que o
   * AudioManager sempre recebe uma resposta dentro de PLAY_WATCHDOG_TIMEOUT_MS.
   *
   * Retorna { ok: true } em sucesso, ou
   * { ok: false, reason: 'timeout' | 'rejected' | 'autoplay_blocked' | 'no_element', error? }
   */
  async playWithWatchdog(element, item = null, options = {}) {
    const label = options.label || "audio";
    const audioId = item?.id ?? item?.spot_id ?? item?.track_id ?? null;
    const url = element?.src || item?.file_url || item?.url || null;
    const startedAt = Date.now();

    if (!element) {
      return { ok: false, reason: "no_element" };
    }

    this._logAudio("PLAY_REQUEST", { label, audioId, url });

    let timeoutId = null;
    const timeoutPromise = new Promise((resolve) => {
      timeoutId = setTimeout(() => resolve({ outcome: "timeout" }), PLAY_WATCHDOG_TIMEOUT_MS);
    });

    // Envolve play() para capturar tanto rejeição assíncrona quanto exceção síncrona
    const playPromise = (async () => {
      try {
        await element.play();
        return { outcome: "success" };
      } catch (error) {
        return { outcome: "rejected", error };
      }
    })();

    const result = await Promise.race([playPromise, timeoutPromise]);
    const elapsedMs = Date.now() - startedAt;

    if (result.outcome === "success") {
      clearTimeout(timeoutId);
      this._logAudio("PLAY_SUCCESS", { label, audioId, url, elapsedMs });
      return { ok: true };
    }

    if (result.outcome === "timeout") {
      this._logAudio("PLAY_TIMEOUT", {
        label,
        audioId,
        url,
        reason: "watchdog_timeout_exceeded",
        elapsedMs,
      });
      if (audioId) this._markAudioFailed(audioId);
      return { ok: false, reason: "timeout" };
    }

    // outcome === 'rejected'
    clearTimeout(timeoutId);
    const error = result.error;
    const errorName = error?.name || "UnknownError";

    this._logAudio("PLAY_REJECTED", {
      label,
      audioId,
      url,
      reason: errorName,
      message: error?.message,
      elapsedMs,
    });

    if (errorName === "NotAllowedError") {
      // Bloqueio de autoplay não é um arquivo quebrado — não entra em
      // quarentena, apenas sinaliza para a UI pedir interação do usuário.
      this._notify({ autoplayBlocked: true });
      return { ok: false, reason: "autoplay_blocked", error };
    }

    if (audioId) this._markAudioFailed(audioId);
    return { ok: false, reason: "rejected", error };
  }

  /**
   * Centraliza a resposta a uma falha de faixa de rádio: marca quarentena,
   * loga SKIP_FAILED_AUDIO e avança para a próxima faixa válida.
   *
   * Guarda contra loop infinito: se o número de pulos consecutivos atingir
   * o tamanho da fila (todas as faixas falharam), entra em estado de erro
   * controlado (SILENT) em vez de continuar girando a fila para sempre.
   */
  _handleRadioTrackFailure(track, reason, { markFailed = true } = {}) {
    const audioId = track?.id ?? null;
    const url = track?.file_url ?? null;

    if (markFailed && audioId) {
      this._markAudioFailed(audioId);
    }

    this._logAudio("SKIP_FAILED_AUDIO", { label: "radio", audioId, url, reason });

    this._radioSkipStreak++;
    const queueLength = this.queue.radio.length;

    if (queueLength > 0 && this._radioSkipStreak >= queueLength) {
      this._logAudio("NO_VALID_AUDIO", {
        label: "radio",
        queueLength,
        reason: "all_tracks_failed_or_quarantined",
      });
      this._radioSkipStreak = 0;
      this._notify({ current: AUDIO_STATE.SILENT, isPlaying: false, currentTrack: null });
      return;
    }

    // Faixa falhou (não terminou naturalmente), mas o fundo já está silencioso
    // — mesma janela de oportunidade que WAIT_SILENCE espera. Toca o spot
    // represado agora em vez de deixá-lo preso até a próxima faixa terminar.
    if (this._pendingSpot) {
      this._playPendingSpotThenAdvance();
      return;
    }

    this.nextTrack();
  }

  /**
   * Fade in suave. Toca o elemento via watchdog (playWithWatchdog) em
   * paralelo com a rampa de volume — preserva o comportamento original, que
   * já iniciava a rampa imediatamente, sem aguardar play() resolver.
   *
   * `item` e `label` são repassados ao watchdog para rastreio/log
   * (audioId, tipo) e para decidir quarentena em caso de falha.
   *
   * Retorna { ok, reason?, error? } — o resultado do watchdog.
   */
  _fadeIn(element, duration = 200, useMutedTrick = true, item = null, label = "audio") {
    if (!element) {
      return Promise.resolve({ ok: true });
    }

    element.volume = 0;

    const fadeAnimation = new Promise((resolve) => {
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

    let playPromise;
    if (useMutedTrick) {
      // Truque de autoplay-mudo: necessário só na 1ª reprodução da página
      // (rádio). Depois disso o navegador já liberou áudio na aba — usar o
      // truque em clipes curtos (spots) arrisca tocar o clipe inteiro mudo,
      // pois o unmute só ocorre quando o watchdog resolve.
      element.muted = true;
      playPromise = this.playWithWatchdog(element, item, { label }).then((result) => {
        element.muted = false;
        return result;
      });
    } else {
      // Garante que o elemento não fique preso em muted=true herdado da
      // criação (ex.: spot.muted = true definido no Player para contornar
      // autoplay caso seja o primeiro áudio da página).
      element.muted = false;
      playPromise = this.playWithWatchdog(element, item, { label });
    }

    return Promise.all([playPromise, fadeAnimation]).then(([result]) => result);
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
      // Faixa terminou: se há spot represado (WAIT_SILENCE), toca-o agora —
      // o fundo está silencioso, exatamente a janela que essa política espera.
      // _playPendingSpotThenAdvance cuida de avançar para a próxima faixa
      // depois (no fim do spot ou se ele falhar ao tocar).
      if (this._pendingSpot) {
        this._playPendingSpotThenAdvance();
        return;
      }
      this.nextTrack();
    }
  }

  /**
   * Toca o spot represado por WAIT_SILENCE e, ao terminar (ou falhar),
   * avança a fila de rádio para a próxima faixa.
   */
  async _playPendingSpotThenAdvance() {
    const pending = this._pendingSpot;
    this._pendingSpot = null;
    if (!pending) {
      this.nextTrack();
      return;
    }

    this.queue.radioIndex++;
    if (this.queue.radioIndex >= this.queue.radio.length) {
      this.queue.radioIndex = 0;
    }

    // previous = SILENT: o fundo já parou (evento 'ended'); _resumeAfterSpot
    // vai então tocar a faixa de rádio já avançada via _playRadioByIndex.
    await this.playSpot(pending.spotUrl, pending.insertionPolicy, pending.spotItem);
    if (this.state.current !== AUDIO_STATE.SPOT) {
      // playSpot não conseguiu tocar (falha/quarentena) — segue o fluxo normal.
      this._playRadioByIndex();
    }
  }

  _onTrackError(source) {
    if (source === 'radio') {
      const track = this.queue.radio[this.queue.radioIndex] || this.state.currentTrack;
      // Roteia pelo guard central (_handleRadioTrackFailure) em vez de chamar
      // nextTrack() diretamente — evita o risco de loop infinito que existia
      // aqui (todo evento "error" nativo avançava sem nenhum limite).
      this._handleRadioTrackFailure(track, "media_error_event");
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
