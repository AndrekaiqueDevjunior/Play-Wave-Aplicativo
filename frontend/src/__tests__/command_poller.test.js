import { beforeEach, describe, expect, it, vi } from "vitest";
import { createCommandPoller } from "../player-core/commandPoller.js";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("command poller", () => {
  it("skips polling when device credentials are missing", async () => {
    const buscarComandosPendentes = vi.fn();
    const marcarComandoRecebido = vi.fn();
    const marcarComandoIniciado = vi.fn();
    const ackComando = vi.fn();
    const executeCommand = vi.fn();

    const poller = createCommandPoller({
      getDeviceId: () => null,
      getDeviceToken: () => null,
      buscarComandosPendentes,
      marcarComandoRecebido,
      marcarComandoIniciado,
      ackComando,
      executeCommand,
      setPhase: vi.fn(),
      setPlaylist: vi.fn(),
      setCurrentIndex: vi.fn(),
      setProgress: vi.fn(),
    });

    await poller.pollCommands();

    expect(buscarComandosPendentes).not.toHaveBeenCalled();
    expect(marcarComandoRecebido).not.toHaveBeenCalled();
    expect(marcarComandoIniciado).not.toHaveBeenCalled();
    expect(ackComando).not.toHaveBeenCalled();
    expect(executeCommand).not.toHaveBeenCalled();
  });

  it("does not reenter while polling is already in progress", async () => {
    const buscarComandosPendentes = vi.fn().mockImplementation(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
      return [{ id: "cmd-1", command_type: "sync", payload: {} }];
    });
    const marcarComandoRecebido = vi.fn().mockResolvedValue(null);
    const marcarComandoIniciado = vi.fn().mockResolvedValue(null);
    const ackComando = vi.fn().mockResolvedValue(null);
    const executeCommand = vi.fn().mockResolvedValue({
      success: true,
      result: {},
    });

    const poller = createCommandPoller({
      getDeviceId: () => "device-1",
      getDeviceToken: () => "token-1",
      buscarComandosPendentes,
      marcarComandoRecebido,
      marcarComandoIniciado,
      ackComando,
      executeCommand,
      setPhase: vi.fn(),
      setPlaylist: vi.fn(),
      setCurrentIndex: vi.fn(),
      setProgress: vi.fn(),
    });

    await Promise.all([poller.pollCommands(), poller.pollCommands()]);

    expect(buscarComandosPendentes).toHaveBeenCalledTimes(1);
    expect(marcarComandoRecebido).toHaveBeenCalledTimes(1);
    expect(marcarComandoIniciado).toHaveBeenCalledTimes(1);
    expect(executeCommand).toHaveBeenCalledTimes(1);
  });
});
