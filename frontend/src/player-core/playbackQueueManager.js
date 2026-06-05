/**
 * PlaybackQueueManager
 * Gerencia a fila de reprodução com suporte a shuffle, loop e persistência.
 * TASK 06: Suporta sequencial, aleatório e aleatório sem repetição.
 */

const STORAGE_KEY = 'playwave_queue_state';

export class PlaybackQueueManager {
  constructor(tracks = [], options = {}) {
    this.originalTracks = [...tracks];
    this.queue = [...tracks];
    this.currentIndex = 0;
    this.shuffleSeed = null;
    this.playedIndices = new Set(); // Para "shuffle sem repetir"

    // Opções
    this.shuffle_enabled = options.shuffle_enabled ?? false;
    this.loop_enabled = options.loop_enabled ?? true;
    this.playback_mode = options.playback_mode ?? 'sequential'; // sequential, shuffle, shuffle_no_repeat

    // Se há estado salvo, restaurar
    this.restoreState();

    // Se está em shuffle, embaralhar
    if (this.shuffle_enabled && this.queue.length > 0) {
      this.shuffleQueue();
    }
  }

  /**
   * Embaralha a fila mantendo seed para reproducibilidade
   */
  shuffleQueue() {
    if (!this.shuffleSeed) {
      this.shuffleSeed = Math.random();
    }

    const seededRandom = this.getSeededRandom(this.shuffleSeed);

    // Fisher-Yates shuffle
    for (let i = this.queue.length - 1; i > 0; i--) {
      const j = Math.floor(seededRandom() * (i + 1));
      [this.queue[i], this.queue[j]] = [this.queue[j], this.queue[i]];
    }
  }

  /**
   * Gerador de números aleatórios determinístico usando seed
   */
  getSeededRandom(seed) {
    return () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };
  }

  /**
   * Obtém a próxima faixa para tocar
   */
  getNext() {
    if (this.queue.length === 0) return null;

    if (this.currentIndex >= this.queue.length) {
      if (this.loop_enabled) {
        this.currentIndex = 0;
        this.playedIndices.clear(); // Reset para novo ciclo
      } else {
        return null; // FIM da fila sem loop
      }
    }

    const track = this.queue[this.currentIndex];
    this.playedIndices.add(this.currentIndex);
    this.currentIndex++;

    this.saveState();
    return track;
  }

  /**
   * Obtém a próxima faixa sem repetição (shuffle_no_repeat)
   */
  getNextNoRepeat() {
    if (this.queue.length === 0) return null;

    // Se já tocou todas, reiniciar
    if (this.playedIndices.size >= this.queue.length) {
      if (this.loop_enabled) {
        this.playedIndices.clear();
        this.currentIndex = 0;
      } else {
        return null; // FIM da fila
      }
    }

    // Encontrar índice não tocado
    let nextIndex = this.currentIndex;
    let attempts = 0;
    while (this.playedIndices.has(nextIndex) && attempts < this.queue.length) {
      nextIndex = Math.floor(Math.random() * this.queue.length);
      attempts++;
    }

    if (attempts >= this.queue.length) {
      // Nenhum índice novo encontrado, reiniciar
      this.playedIndices.clear();
      nextIndex = 0;
    }

    this.currentIndex = nextIndex;
    this.playedIndices.add(nextIndex);
    const track = this.queue[nextIndex];
    this.currentIndex = (nextIndex + 1) % this.queue.length;

    this.saveState();
    return track;
  }

  /**
   * Pula para próxima faixa manualmente
   */
  skipToNext() {
    if (this.playback_mode === 'shuffle_no_repeat') {
      return this.getNextNoRepeat();
    }
    return this.getNext();
  }

  /**
   * Volta para faixa anterior
   */
  skipToPrevious() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
    } else if (this.loop_enabled) {
      this.currentIndex = this.queue.length - 1;
    }
    this.saveState();
    return this.queue[this.currentIndex] || null;
  }

  /**
   * Salta para um índice específico
   */
  jumpToIndex(index) {
    if (index >= 0 && index < this.queue.length) {
      this.currentIndex = index;
      this.playedIndices.add(index);
      this.saveState();
      return this.queue[index];
    }
    return null;
  }

  /**
   * Atualiza opções de reprodução
   */
  updateOptions(options) {
    const oldShuffle = this.shuffle_enabled;

    this.shuffle_enabled = options.shuffle_enabled ?? this.shuffle_enabled;
    this.loop_enabled = options.loop_enabled ?? this.loop_enabled;
    this.playback_mode = options.playback_mode ?? this.playback_mode;

    // Se mudou de não-shuffle para shuffle
    if (!oldShuffle && this.shuffle_enabled) {
      this.playedIndices.clear();
      this.shuffleQueue();
      this.currentIndex = 0;
    }

    this.saveState();
  }

  /**
   * Salva estado da fila em localStorage
   */
  saveState() {
    const state = {
      queueIds: this.queue.map(t => t.id),
      currentIndex: this.currentIndex,
      playedIndices: Array.from(this.playedIndices),
      shuffleSeed: this.shuffleSeed,
      shuffle_enabled: this.shuffle_enabled,
      loop_enabled: this.loop_enabled,
      playback_mode: this.playback_mode,
      timestamp: Date.now(),
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  /**
   * Restaura estado da fila de localStorage
   */
  restoreState() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return;

    try {
      const state = JSON.parse(stored);

      // Validar se os tracks ainda são os mesmos
      const storedIds = state.queueIds;
      const currentIds = this.originalTracks.map(t => t.id);

      if (JSON.stringify(storedIds) !== JSON.stringify(currentIds)) {
        // Fila mudou, não restaurar
        localStorage.removeItem(STORAGE_KEY);
        return;
      }

      this.currentIndex = state.currentIndex || 0;
      this.playedIndices = new Set(state.playedIndices || []);
      this.shuffleSeed = state.shuffleSeed;
      this.shuffle_enabled = state.shuffle_enabled ?? false;
      this.loop_enabled = state.loop_enabled ?? true;
      this.playback_mode = state.playback_mode ?? 'sequential';

      // Se estava em shuffle, reconstruir fila
      if (this.shuffle_enabled && this.shuffleSeed) {
        this.queue = [...this.originalTracks];
        this.shuffleQueue();
      }
    } catch (e) {
      console.warn('[PlaybackQueueManager] Failed to restore state:', e);
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  /**
   * Limpa estado salvo
   */
  clearState() {
    localStorage.removeItem(STORAGE_KEY);
    this.playedIndices.clear();
    this.currentIndex = 0;
    this.shuffleSeed = null;
  }

  /**
   * Retorna informações da fila
   */
  getQueueInfo() {
    return {
      totalTracks: this.queue.length,
      currentIndex: this.currentIndex,
      currentTrackId: this.queue[this.currentIndex]?.id,
      queueIds: this.queue.map(t => t.id),
      playedCount: this.playedIndices.size,
      shuffle_enabled: this.shuffle_enabled,
      loop_enabled: this.loop_enabled,
      playback_mode: this.playback_mode,
    };
  }

  /**
   * Atualiza a fila com novos tracks
   */
  updateTracks(newTracks) {
    this.originalTracks = [...newTracks];
    this.queue = [...newTracks];
    this.currentIndex = 0;
    this.playedIndices.clear();
    this.shuffleSeed = null;

    if (this.shuffle_enabled) {
      this.shuffleQueue();
    }

    this.saveState();
  }
}

export default PlaybackQueueManager;
