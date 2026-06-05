/**
 * Testes para PlaybackQueueManager
 * TASK 06: Shuffle, Loop, Persistência de Fila
 */

import { PlaybackQueueManager } from '../player-core/playbackQueueManager';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => {
      store[key] = value.toString();
    },
    removeItem: (key) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

global.localStorage = localStorageMock;

describe('PlaybackQueueManager', () => {
  const mockTracks = [
    { id: '1', name: 'Track 1' },
    { id: '2', name: 'Track 2' },
    { id: '3', name: 'Track 3' },
    { id: '4', name: 'Track 4' },
  ];

  beforeEach(() => {
    localStorage.clear();
  });

  test('sequential playback - getNext retorna faixas em ordem', () => {
    const qm = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: false,
      loop_enabled: false,
    });

    expect(qm.getNext()).toEqual(mockTracks[0]);
    expect(qm.getNext()).toEqual(mockTracks[1]);
    expect(qm.getNext()).toEqual(mockTracks[2]);
    expect(qm.getNext()).toEqual(mockTracks[3]);
    expect(qm.getNext()).toBeNull(); // Sem loop
  });

  test('sequential playback com loop', () => {
    const qm = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: false,
      loop_enabled: true,
    });

    // Ir até o fim
    qm.getNext();
    qm.getNext();
    qm.getNext();
    qm.getNext();

    // Volta ao início
    expect(qm.getNext()).toEqual(mockTracks[0]);
  });

  test('shuffle embaralha a fila de forma determinística', () => {
    const qm1 = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: true,
      loop_enabled: false,
    });

    const shuffleSeed = qm1.shuffleSeed;
    const order1 = [];
    let track = qm1.getNext();
    while (track) {
      order1.push(track.id);
      track = qm1.getNext();
    }

    // Criar outro com mesmo seed simulado
    localStorage.clear();
    const qm2 = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: true,
      loop_enabled: false,
    });
    qm2.shuffleSeed = shuffleSeed;
    qm2.shuffleQueue();

    const order2 = [];
    track = qm2.getNext();
    while (track) {
      order2.push(track.id);
      track = qm2.getNext();
    }

    expect(order1).toEqual(order2);
  });

  test('shuffle sem repetição - não repete até completar ciclo', () => {
    const qm = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: true,
      loop_enabled: false,
      playback_mode: 'shuffle_no_repeat',
    });

    const tracks = [];
    for (let i = 0; i < mockTracks.length; i++) {
      const t = qm.getNextNoRepeat();
      if (t) tracks.push(t.id);
    }

    // Deve ter todos os 4 IDs únicos
    expect(new Set(tracks).size).toBe(4);
  });

  test('persistência de estado em localStorage', () => {
    const qm1 = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: true,
      loop_enabled: true,
    });

    qm1.getNext();
    qm1.getNext();
    const state1 = qm1.getQueueInfo();

    // Criar novo QueueManager - deve restaurar estado
    const qm2 = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: true,
      loop_enabled: true,
    });
    const state2 = qm2.getQueueInfo();

    expect(state2.currentIndex).toBe(state1.currentIndex);
    expect(state2.playedCount).toBe(state1.playedCount);
  });

  test('jumpToIndex pula para índice específico', () => {
    const qm = new PlaybackQueueManager(mockTracks);

    const track = qm.jumpToIndex(2);
    expect(track).toEqual(mockTracks[2]);
    expect(qm.currentIndex).toBe(3); // Próximo será o index 3
  });

  test('updateTracks reseta fila', () => {
    const qm = new PlaybackQueueManager(mockTracks);

    qm.getNext();
    qm.getNext();

    const newTracks = [
      { id: 'A', name: 'Track A' },
      { id: 'B', name: 'Track B' },
    ];

    qm.updateTracks(newTracks);

    const info = qm.getQueueInfo();
    expect(info.totalTracks).toBe(2);
    expect(info.currentIndex).toBe(0);
    expect(info.playedCount).toBe(0);
  });

  test('clearState limpa localStorage e resets', () => {
    const qm = new PlaybackQueueManager(mockTracks);
    qm.getNext();
    qm.getNext();

    qm.clearState();

    const info = qm.getQueueInfo();
    expect(info.currentIndex).toBe(0);
    expect(info.playedCount).toBe(0);
    expect(localStorage.getItem('playwave_queue_state')).toBeNull();
  });

  test('skipToNext respeta playback_mode', () => {
    const qm = new PlaybackQueueManager(mockTracks, {
      shuffle_enabled: false,
      loop_enabled: true,
      playback_mode: 'sequential',
    });

    // Skip deve chamar getNext (sequencial)
    qm.skipToNext();
    expect(qm.currentIndex).toBe(1);
  });

  test('skipToPrevious volta para faixa anterior', () => {
    const qm = new PlaybackQueueManager(mockTracks);
    qm.jumpToIndex(2);

    const prev = qm.skipToPrevious();
    expect(prev).toEqual(mockTracks[1]);
  });
});
