/**
 * Smart Playlist Updater — Atualiza playlist sem interromper playback
 * TASK 21: Player recalcula fila sem reiniciar
 *
 * Estratégia:
 * 1. Track atual continua tocando
 * 2. Próximos tracks são refetch do servidor
 * 3. Se campanha mudou, obter nova campanha
 * 4. Se folder horário mudou, atualizar folder ativo
 */

import { logEvent, EventType } from './eventLogger';

export class SmartPlaylistUpdater {
  constructor(apiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Atualiza playlist inteligentemente quando config muda
   *
   * @param {object} params
   * @param {string} params.deviceId - ID do dispositivo
   * @param {string} params.currentTrackId - Track sendo tocado agora (não interromper)
   * @param {string} params.playlistId - ID da playlist atual
   * @param {object} params.onPlaylistUpdate - Callback com nova playlist
   */
  async updatePlaylist({
    deviceId,
    currentTrackId,
    playlistId,
    onPlaylistUpdate,
  }) {
    try {
      console.log(
        '[SmartPlaylistUpdater] Updating playlist for device',
        deviceId
      );

      // Obter novo estado do dispositivo (inclui campanha, playlist, folder ativo)
      const deviceResponse = await this.apiClient.get(`/devices/${deviceId}`);

      // Obter nova campanha/playlist
      let newPlaylist = null;

      if (deviceResponse.campaign_id) {
        // Dispositivo tem campanha
        const campaignResponse = await this.apiClient.get(
          `/campaigns/${deviceResponse.campaign_id}`
        );
        newPlaylist = campaignResponse;
      } else if (deviceResponse.audio_playlist_id) {
        // Dispositivo tem playlist sonora (rádio)
        const playlistResponse = await this.apiClient.get(
          `/audio/playlists/${deviceResponse.audio_playlist_id}`
        );
        newPlaylist = playlistResponse;
      }

      if (!newPlaylist) {
        console.warn('[SmartPlaylistUpdater] No playlist found');
        return;
      }

      // Log evento de atualização
      logEvent(EventType.PLAYER_SCHEDULE_UPDATED, {
        deviceId,
        playlistId: newPlaylist.id,
        details: {
          reason: 'config_version_changed',
          current_track_preserved: !!currentTrackId,
        },
      });

      // Callback com nova playlist
      if (onPlaylistUpdate) {
        onPlaylistUpdate({
          playlist: newPlaylist,
          currentTrackIdToPreserve: currentTrackId,
        });
      }
    } catch (error) {
      console.error('[SmartPlaylistUpdater] Error updating playlist:', error);
      throw error;
    }
  }

  /**
   * Valida se track atual ainda é válido na nova playlist
   */
  isTrackStillValid(trackId, newPlaylist) {
    if (!newPlaylist || !newPlaylist.media_ids) {
      return false;
    }

    return newPlaylist.media_ids.includes(trackId);
  }

  /**
   * Encontra próximo track na nova playlist após o track atual
   */
  getNextTrackAfter(trackId, newPlaylist) {
    if (!newPlaylist || !newPlaylist.media_ids) {
      return null;
    }

    const index = newPlaylist.media_ids.indexOf(trackId);
    if (index === -1 || index === newPlaylist.media_ids.length - 1) {
      return null; // Último ou não encontrado
    }

    return newPlaylist.media_ids[index + 1];
  }
}

export default SmartPlaylistUpdater;
