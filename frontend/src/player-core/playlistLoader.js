/**
 * Playlist Loader — Carrega playlist com validação de cache
 * TASK 33: Integração de cache versionado
 *
 * Fluxo:
 * 1. Chamar loadPlaylist(deviceId, token, apiClient, cacheManager)
 * 2. Valida versão de campaign/playlist se em cache
 * 3. Se versão bate: usa cache (rápido)
 * 4. Se versão diferente: busca do servidor (fresco)
 * 5. Salva nova versão em cache
 * 6. Retorna playlist completa
 */

import { logEvent, EventType } from './eventLogger';

export async function loadPlaylistWithCache({
  deviceId,
  apiClient,
  cacheManager,
  getDevicePlaylistFn, // getDevicePlaylist from @/lib/api
}) {
  try {
    console.log('[playlistLoader] Loading playlist with cache validation');

    // 1. Buscar info do device (inclui campaign_id, campaign_version)
    const deviceResponse = await apiClient.get(`/devices/${deviceId}`);
    const campaignId = deviceResponse.campaign_id;
    const audioPlaylistId = deviceResponse.audio_playlist_id;

    // 2. Se tem campaign: validar versão com cache
    if (campaignId && cacheManager) {
      const campaign = await cacheManager.getCampaignWithVersionCheck(campaignId);
      console.log('[playlistLoader] Campaign loaded:', {
        id: campaign.id,
        version: campaign.campaign_version,
      });
    }

    // 3. Se tem playlist de áudio: validar versão com cache
    if (audioPlaylistId && cacheManager) {
      const playlist = await cacheManager.getPlaylistWithVersionCheck(audioPlaylistId);
      console.log('[playlistLoader] AudioPlaylist loaded:', {
        id: playlist.id,
        version: playlist.version,
      });
    }

    // 4. Carregar playlist completa (faz GET /devices/{id}/playlist)
    // Se o cache foi validado acima, espera-se que o servidor retorne
    // dados consistentes (caso contrário, cacheManager descartou o cache antigo)
    const playlistResponse = await getDevicePlaylistFn(deviceId);

    console.log('[playlistLoader] Playlist loaded successfully:', {
      campaignId: playlistResponse.campaign?.id,
      mediaCount: playlistResponse.media?.length,
      audioPlaylistId: playlistResponse.audio_playlist?.id,
      trackCount: playlistResponse.audio_playlist?.track_ids?.length,
    });

    logEvent(EventType.RADIO_PLAYLIST_LOADED, {
      deviceId,
      playlistId: playlistResponse.campaign?.id || playlistResponse.audio_playlist?.id,
      details: {
        media_count: playlistResponse.media?.length || 0,
        track_count: playlistResponse.audio_playlist?.track_ids?.length || 0,
      },
    });

    return playlistResponse;
  } catch (error) {
    console.error('[playlistLoader] Error loading playlist:', error);
    throw error;
  }
}

/**
 * Invalidar cache quando comando clear_cache é executado
 */
export function invalidateCacheForDevice(cacheManager, campaignId, audioPlaylistId) {
  if (!cacheManager) return;

  if (campaignId) {
    cacheManager.invalidateCampaignCache(campaignId);
  }
  if (audioPlaylistId) {
    cacheManager.invalidatePlaylistCache(audioPlaylistId);
  }

  console.log('[playlistLoader] Cache invalidated for device');

  logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
    details: {
      reason: 'manual_invalidation',
      campaign_id: campaignId,
      playlist_id: audioPlaylistId,
    },
  });
}

export default { loadPlaylistWithCache, invalidateCacheForDevice };
