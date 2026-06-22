// @ts-nocheck
/**
 * contentGuard.js — SPEC 015
 *
 * Decide se há conteúdo "em exibição" no player agora, e permite registrar um
 * callback de uma vez (one-shot) para ser avisado quando o conteúdo atual
 * terminar. Usado pelos schedulers de minimizar (windowExposureScheduler,
 * desktopExposureTimeScheduler) para nunca cortar vídeo/campanha no meio —
 * política padrão WAIT_CONTENT_END do SPEC-007 do documento mestre.
 *
 * Não sabe nada sobre mídia/playlist — apenas observa os sinais que o
 * Player.jsx já produz (phase, playlist, currentIndex, startTime, duration) e
 * o evento de "avançou para a próxima mídia" (toda chamada real a
 * advanceMedia significa que o conteúdo anterior terminou).
 */

export function createContentGuard() {
  let snapshot = {
    phase: "waiting",
    hasPlaylist: false,
    endsAt: null, // timestamp absoluto (ms) de fim estimado, ou null se desconhecido (duração natural)
  };
  const listeners = new Set();

  /**
   * Atualiza o snapshot do estado atual de reprodução. Chamado pelo Player a
   * cada troca de mídia/fase.
   */
  const update = ({ phase, hasPlaylist, endsAt = null }) => {
    snapshot = { phase, hasPlaylist: Boolean(hasPlaylist), endsAt };
  };

  /**
   * true quando há conteúdo "protegido" tocando agora — fora da fase
   * "playing" (ex.: tela de pareamento, loading, apenas rádio sem mídia
   * visual) não há nada para esperar terminar.
   */
  const isContentBusy = () => snapshot.phase === "playing" && snapshot.hasPlaylist;

  /**
   * Estimativa de quanto falta (ms) para o conteúdo atual terminar.
   * Retorna null quando desconhecido (mídia de duração natural, sem
   * temporizador) ou quando não há conteúdo ativo.
   */
  const getRemainingMs = () => {
    if (!isContentBusy() || snapshot.endsAt == null) return null;
    return Math.max(0, snapshot.endsAt - Date.now());
  };

  /**
   * Chamado pelo Player sempre que o conteúdo atual termina e avança para o
   * próximo item (advanceMedia). Dispara e limpa todos os callbacks
   * registrados via onceContentEnd.
   */
  const notifyContentEnded = () => {
    const toRun = Array.from(listeners);
    listeners.clear();
    toRun.forEach((cb) => {
      try {
        cb();
      } catch {
        /* callback não deve interromper os demais */
      }
    });
  };

  /**
   * Registra `callback` para ser chamado uma única vez quando o conteúdo
   * atual terminar. Se não houver conteúdo ativo agora, chama imediatamente
   * (nada para esperar).
   */
  const onceContentEnd = (callback) => {
    if (!isContentBusy()) {
      callback();
      return () => {};
    }
    listeners.add(callback);
    return () => listeners.delete(callback);
  };

  return { update, isContentBusy, getRemainingMs, notifyContentEnded, onceContentEnd };
}
