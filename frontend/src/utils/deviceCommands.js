/**
 * deviceCommands.js — Labels e estilos compartilhados para comandos de
 * dispositivo. Usado por DispositivoDetalhe e CommandHistoryTimeline.
 *
 * SPEC 003 — centraliza a tradução de `command_type` e `status` para
 * apresentação consistente.
 */

export const COMMAND_LABELS = {
  sync:             "Sincronizar",
  refresh_playlist: "Atualizar Playlist",
  clear_cache:      "Limpar Cache",
  reload_player:    "Recarregar Player",
  minimize_player:  "Minimizar Player",
  restore_player:   "Restaurar Player",
  show_desktop:     "Mostrar Desktop",
  restart_app:      "Reiniciar App",
  restart:          "Reiniciar App",
  restart_device:   "Reiniciar Dispositivo",
  shutdown_device:  "Desligar Dispositivo",
  screenshot:       "Capturar Tela",
  take_screenshot:  "Capturar Tela",
  set_volume:       "Ajustar Volume",
  mute:             "Silenciar",
  unmute:           "Ativar Som",
};

/**
 * `group`: "operational" | "reset" | "power"
 * Operacionais são seguros (só recarregam dados/state). "reset" reinicia o
 * app. "power" reinicia ou desliga o dispositivo físico.
 */
export const COMMANDS_BY_GROUP = {
  operational: [
    { command: "sync",             label: "Sincronizar",       tooltip: "Recarrega playlist sem reiniciar o player." },
    { command: "refresh_playlist", label: "Atualizar Playlist", tooltip: "Mesmo que Sincronizar." },
    { command: "clear_cache",      label: "Limpar Cache",      tooltip: "Limpa cache local (IndexedDB) e recarrega." },
    { command: "reload_player",    label: "Recarregar Player", tooltip: "Recarrega a página do player." },
  ],
  reset: [
    { command: "restart_app", label: "Reiniciar App", tooltip: "Encerra e reabre o app (Electron) ou recreate da Activity (Android). Web puro: não suportado." },
  ],
  window: [
    { command: "minimize_player", label: "Minimizar", tooltip: "Minimiza a janela do Player. Suportado inicialmente em Electron Windows/Linux." },
    { command: "restore_player", label: "Restaurar", tooltip: "Restaura e foca a janela do Player Electron." },
    {
      command: "show_desktop",
      label: "Mostrar desktop",
      tooltip: "Minimiza temporariamente e restaura automaticamente em 10 segundos.",
      payload: { duration_seconds: 10 },
      expiresInSeconds: 300,
    },
  ],
  power: [
    { command: "restart_device",  label: "Reiniciar Dispositivo", tooltip: "Reboot físico do OS. Requer sudo (Linux), Admin (Windows) ou Device Owner (Android)." },
    { command: "shutdown_device", label: "Desligar Dispositivo",  tooltip: "Desliga fisicamente. Mesmas restrições. Android stock: apenas bloqueia a tela." },
  ],
};

export const STATUS_LABELS = {
  pending:   { label: "Aguardando envio",   className: "bg-slate-100 text-slate-700 border-slate-200" },
  sent:      { label: "Enviado",             className: "bg-sky-100 text-sky-700 border-sky-200" },
  received:  { label: "Recebido",            className: "bg-blue-100 text-blue-700 border-blue-200" },
  executing: { label: "Executando",          className: "bg-amber-100 text-amber-800 border-amber-200" },
  completed: { label: "Concluído",           className: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  executed:  { label: "Concluído",           className: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  failed:    { label: "Falhou",              className: "bg-red-100 text-red-700 border-red-200" },
  expired:   { label: "Expirou",             className: "bg-slate-100 text-slate-500 border-slate-200" },
  cancelled: { label: "Cancelado",           className: "bg-purple-100 text-purple-700 border-purple-200" },
};

/**
 * Resolve label/cor do status considerando `platform_unsupported` (que
 * tecnicamente é `failed` mas merece apresentação diferenciada).
 */
export function statusBadgeFor(command) {
  if (
    command?.status === "failed" &&
    command?.result?.platform_unsupported
  ) {
    return {
      label: "Não suportado",
      className: "bg-slate-200 text-slate-600 border-slate-300",
    };
  }
  return STATUS_LABELS[command?.status] || {
    label: command?.status || "—",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  };
}

export function commandLabel(commandType) {
  return COMMAND_LABELS[commandType] || commandType;
}

export const DESTRUCTIVE_COMMAND_TYPES = new Set([
  "restart_app",
  "restart_device",
  "shutdown_device",
  "factory_reset",
  "reboot",
]);

export function isDestructive(commandType) {
  return DESTRUCTIVE_COMMAND_TYPES.has(commandType);
}
