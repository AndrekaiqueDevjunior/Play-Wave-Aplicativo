/**
 * Cache Command Handler — Processa comando clear_cache
 * TASK 33: Botão "Limpar cache" no gerenciador envia comando remoto
 *
 * Fluxo:
 * 1. Admin clica "Limpar cache" no gerenciador
 * 2. Envia comando POST /devices/{id}/command {type: "clear_cache"}
 * 3. Backend retorna command_id
 * 4. Player recebe evento de novo comando via SSE ou polling
 * 5. Player executa clearAllCache() no PlaylistCacheManager
 * 6. Player responde com ACK
 */

import { logEvent, EventType, logCommandReceived, logCommandExecuted } from './eventLogger';

export class CacheCommandHandler {
  constructor(deviceId, apiClient, cacheManager) {
    this.deviceId = deviceId;
    this.apiClient = apiClient;
    this.cacheManager = cacheManager;
  }

  /**
   * Enviar comando clear_cache do dashboard/gerenciador
   *
   * Chamado quando admin clica "Limpar cache" na UI
   */
  async sendClearCacheCommand() {
    try {
      console.log('[CacheCommandHandler] Sending clear_cache command');

      const response = await this.apiClient.post(`/devices/${this.deviceId}/command`, {
        command_type: 'clear_cache',
      });

      console.log('[CacheCommandHandler] Command sent:', response.id);

      return {
        success: true,
        commandId: response.id,
        commandType: 'clear_cache',
      };
    } catch (error) {
      console.error('[CacheCommandHandler] Error sending command:', error);
      throw error;
    }
  }

  /**
   * Processar comando clear_cache recebido do servidor
   *
   * Chamado quando player recebe novo comando via SSE/polling
   */
  async handleClearCacheCommand(command) {
    try {
      console.log('[CacheCommandHandler] Processing clear_cache command:', command.id);

      // Log evento
      logCommandReceived(this.deviceId, 'clear_cache', command.id);

      // Executar limpeza de cache
      const clearedCount = this.cacheManager.clearAllCache();

      // Log evento de execução
      logCommandExecuted(this.deviceId, 'clear_cache', command.id);

      console.log('[CacheCommandHandler] Cache cleared successfully:', clearedCount, 'entries');

      return {
        success: true,
        commandId: command.id,
        clearedEntries: clearedCount,
      };
    } catch (error) {
      console.error('[CacheCommandHandler] Error clearing cache:', error);

      logEvent(EventType.PLAYER_COMMAND_FAILED, {
        deviceId: this.deviceId,
        details: {
          command_type: 'clear_cache',
          command_id: command.id,
          error_reason: error.message,
        },
      });

      throw error;
    }
  }

  /**
   * Obter estatísticas de cache (para mostrar no dashboard)
   */
  getCacheStats() {
    return this.cacheManager.getCacheStats();
  }
}

export default CacheCommandHandler;
