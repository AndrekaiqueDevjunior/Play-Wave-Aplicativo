import { DESTRUCTIVE_COMMANDS } from "./commands.js";
import Platform from "./platform.js";

/**
 * createCommandPoller - encapsula polling de comandos com proteção contra
 * reentrância e ACKs pré/post execução para comandos destrutivos.
 */
export function createCommandPoller({
  getDeviceId,
  getDeviceToken,
  buscarComandosPendentes,
  marcarComandoRecebido,
  marcarComandoIniciado,
  ackComando,
  executeCommand,
  setPhase,
  setPlaylist,
  setCurrentIndex,
  setProgress,
}) {
  const running = { current: false };

  async function pollCommands() {
    const deviceId = getDeviceId?.();
    const token = getDeviceToken?.();
    if (!deviceId || !token) return;
    if (running.current) return;
    running.current = true;

    try {
      const commands = await buscarComandosPendentes(deviceId, token);
      if (!commands || commands.length === 0) return;

      for (const cmd of commands) {
        const isDestructive = DESTRUCTIVE_COMMANDS.has(cmd.command_type);
        console.log(
          "[player] executing command:",
          cmd.command_type,
          cmd.id,
          isDestructive ? "(destructive)" : "",
        );

        await marcarComandoRecebido(deviceId, cmd.id, token).catch(() => {});
        await marcarComandoIniciado(deviceId, cmd.id, token).catch(() => {});

        if (isDestructive) {
          await ackComando(deviceId, cmd.id, token, true, null, {
            platform: Platform.name,
            command_type: cmd.command_type,
            ack_phase: "pre_execution",
            completed_at: new Date().toISOString(),
          }).catch((err) => console.warn("[player] pre-ACK failed:", err));
        }

        const result = await executeCommand(cmd, {
          deviceId,
          setPhase,
          setPlaylist,
          setCurrentIndex,
          setProgress,
        });

        if (!isDestructive) {
          await ackComando(
            deviceId,
            cmd.id,
            token,
            result.success,
            result.errorMessage,
            { ...(result.result || {}), ack_phase: "post_execution" },
          );
        } else if (!result.success) {
          await ackComando(
            deviceId,
            cmd.id,
            token,
            false,
            result.errorMessage,
            {
              ...(result.result || {}),
              ack_phase: "post_execution_override",
            },
          );
        }

        console.log(
          "[player] command ACK sent:",
          cmd.id,
          result.success ? "success" : "failed",
        );
      }
    } catch (err) {
      console.warn("[player] poll commands error:", err);
    } finally {
      running.current = false;
    }
  }

  return {
    pollCommands,
  };
}
