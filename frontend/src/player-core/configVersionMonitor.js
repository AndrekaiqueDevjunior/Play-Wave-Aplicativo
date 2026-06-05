/**
 * Config Version Monitor — Monitora mudanças de versão (TASK 31)
 *
 * Monitora:
 * - device.schedule_version (geral de agendamento)
 * - campaign.campaign_version (mídia da campanha)
 * - audio_playlist.version (tracks da playlist)
 *
 * Estratégia:
 * 1. Comparar versões locais vs remotas
 * 2. Se mudou: refetch apenas o necessário (campaign/playlist)
 * 3. Manter track atual tocando, atualizar fila
 */

import { logEvent, EventType, logCacheInvalidated } from './eventLogger';

const MONITOR_INTERVAL_MS = 5000; // Check a cada 5 segundos

export class ConfigVersionMonitor {
  constructor(deviceId, apiClient) {
    this.deviceId = deviceId;
    this.apiClient = apiClient;
    this.localVersions = {
      scheduleVersion: 0,
      campaignVersion: 0,
      playlistVersion: 0,
    };
    this.monitorInterval = null;
    this.onConfigChanged = null;
  }

  /**
   * Inicia monitoramento de versão
   */
  start(onConfigChanged) {
    if (this.monitorInterval) {
      console.warn('[ConfigVersionMonitor] Already started');
      return;
    }

    this.onConfigChanged = onConfigChanged;
    console.log('[ConfigVersionMonitor] Starting version monitor for device', this.deviceId);

    // Verificar imediatamente
    this.checkVersion();

    // Depois periodicamente
    this.monitorInterval = setInterval(() => {
      this.checkVersion();
    }, MONITOR_INTERVAL_MS);
  }

  /**
   * Para o monitoramento
   */
  stop() {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
      console.log('[ConfigVersionMonitor] Stopped');
    }
  }

  /**
   * Verifica versões remotas e dispara callback se alguma mudou
   */
  async checkVersion() {
    try {
      const response = await this.apiClient.get(`/devices/${this.deviceId}`);

      const remoteVersions = {
        scheduleVersion: response.schedule_version || 0,
        campaignVersion: response.campaign_version || 0,
        playlistVersion: response.audio_playlist_version || 0,
      };

      if (!this.localVersions.scheduleVersion) {
        // Primeira vez: apenas cachear versões
        this.localVersions = remoteVersions;
        console.log('[ConfigVersionMonitor] Initial versions:', this.localVersions);
        return;
      }

      // Verificar se algo mudou
      const changed = {
        schedule: remoteVersions.scheduleVersion !== this.localVersions.scheduleVersion,
        campaign: remoteVersions.campaignVersion !== this.localVersions.campaignVersion,
        playlist: remoteVersions.playlistVersion !== this.localVersions.playlistVersion,
      };

      if (changed.schedule || changed.campaign || changed.playlist) {
        console.log('[ConfigVersionMonitor] Versions changed:', {
          schedule: changed.schedule ? `${this.localVersions.scheduleVersion} → ${remoteVersions.scheduleVersion}` : 'unchanged',
          campaign: changed.campaign ? `${this.localVersions.campaignVersion} → ${remoteVersions.campaignVersion}` : 'unchanged',
          playlist: changed.playlist ? `${this.localVersions.playlistVersion} → ${remoteVersions.playlistVersion}` : 'unchanged',
        });

        // Log evento
        if (changed.schedule) {
          logCacheInvalidated(
            this.deviceId,
            'schedule_version_changed',
            this.localVersions.scheduleVersion,
            remoteVersions.scheduleVersion
          );
        }
        if (changed.campaign) {
          logCacheInvalidated(
            this.deviceId,
            'campaign_version_changed',
            this.localVersions.campaignVersion,
            remoteVersions.campaignVersion
          );
        }
        if (changed.playlist) {
          logCacheInvalidated(
            this.deviceId,
            'playlist_version_changed',
            this.localVersions.playlistVersion,
            remoteVersions.playlistVersion
          );
        }

        const oldVersions = { ...this.localVersions };
        this.localVersions = remoteVersions;

        // Disparar callback
        if (this.onConfigChanged) {
          this.onConfigChanged({
            oldVersions,
            newVersions: remoteVersions,
            changed,
            device: response,
          });
        }
      }
    } catch (error) {
      console.error('[ConfigVersionMonitor] Error checking version:', error);
      // Continuar tentando mesmo em erro
    }
  }

  /**
   * Retorna versões atuais
   */
  getVersions() {
    return { ...this.localVersions };
  }
}

/**
 * Hook para usar ConfigVersionMonitor em componentes React
 */
export function useConfigVersionMonitor(deviceId, apiClient, onConfigChanged) {
  const [monitor] = React.useState(() => new ConfigVersionMonitor(deviceId, apiClient));

  React.useEffect(() => {
    monitor.start(onConfigChanged);
    return () => monitor.stop();
  }, [monitor, onConfigChanged]);

  return monitor;
}

export default ConfigVersionMonitor;
