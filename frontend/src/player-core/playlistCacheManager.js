/**
 * Playlist Cache Manager — Cache versionado de programação
 * TASK 33: Cache controlado no player
 *
 * Estratégia:
 * 1. Salvar campaign/playlist com versão no localStorage
 * 2. Validar versão ao carregar (comparar com servidor)
 * 3. Se versão mudou: descartar cache, buscar do servidor
 * 4. Se versão igual: usar cache (mais rápido)
 * 5. Fallback: sempre preferir servidor em caso de erro
 */

import { logEvent, EventType } from './eventLogger';

const CACHE_PREFIX = 'playwave_cache_';
const CACHE_TTL_MINUTES = 60; // Cache expira em 1 hora

export class PlaylistCacheManager {
  constructor(deviceId, apiClient) {
    this.deviceId = deviceId;
    this.apiClient = apiClient;
  }

  /**
   * Obter campaign com validação de versão
   *
   * Estratégia:
   * 1. Verificar versão no servidor
   * 2. Se cache existe e versão bate: retornar cache
   * 3. Se cache não existe ou versão mudou: buscar do servidor
   * 4. Salvar nova versão em cache
   */
  async getCampaignWithVersionCheck(campaignId) {
    try {
      // Obter versão do servidor
      const serverCampaign = await this.apiClient.get(`/campaigns/${campaignId}`);
      const serverVersion = serverCampaign.campaign_version || 0;

      const cacheKey = `${CACHE_PREFIX}campaign_${campaignId}`;
      const cached = this._loadCache(cacheKey);

      if (cached && cached.version === serverVersion && !this._isCacheExpired(cached)) {
        // Cache válido
        console.log('[PlaylistCacheManager] Using cached campaign', {
          campaignId,
          version: serverVersion,
          age: Date.now() - cached.timestamp,
        });

        logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
          deviceId: this.deviceId,
          details: {
            reason: 'cache_hit_campaign',
            version: serverVersion,
          },
        });

        return cached.data;
      }

      // Cache inválido ou não existe
      if (cached) {
        console.log('[PlaylistCacheManager] Cache invalidated for campaign', {
          campaignId,
          oldVersion: cached.version,
          newVersion: serverVersion,
        });

        logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
          deviceId: this.deviceId,
          details: {
            reason: 'campaign_version_changed',
            old_version: cached.version,
            new_version: serverVersion,
          },
        });
      }

      // Salvar nova versão em cache
      this._saveCache(cacheKey, {
        data: serverCampaign,
        version: serverVersion,
        timestamp: Date.now(),
      });

      return serverCampaign;
    } catch (error) {
      console.error('[PlaylistCacheManager] Error getting campaign:', error);

      // Tentar usar cache mesmo que expirado (fallback)
      const cacheKey = `${CACHE_PREFIX}campaign_${campaignId}`;
      const cached = this._loadCache(cacheKey);
      if (cached) {
        console.warn('[PlaylistCacheManager] Using stale cache due to server error');
        return cached.data;
      }

      throw error;
    }
  }

  /**
   * Obter audio playlist com validação de versão
   */
  async getPlaylistWithVersionCheck(playlistId) {
    try {
      // Obter versão do servidor
      const serverPlaylist = await this.apiClient.get(`/audio/playlists/${playlistId}`);
      const serverVersion = serverPlaylist.version || 0;

      const cacheKey = `${CACHE_PREFIX}playlist_${playlistId}`;
      const cached = this._loadCache(cacheKey);

      if (cached && cached.version === serverVersion && !this._isCacheExpired(cached)) {
        // Cache válido
        console.log('[PlaylistCacheManager] Using cached playlist', {
          playlistId,
          version: serverVersion,
          age: Date.now() - cached.timestamp,
        });

        logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
          deviceId: this.deviceId,
          details: {
            reason: 'cache_hit_playlist',
            version: serverVersion,
          },
        });

        return cached.data;
      }

      // Cache inválido ou não existe
      if (cached) {
        console.log('[PlaylistCacheManager] Cache invalidated for playlist', {
          playlistId,
          oldVersion: cached.version,
          newVersion: serverVersion,
        });

        logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
          deviceId: this.deviceId,
          details: {
            reason: 'playlist_version_changed',
            old_version: cached.version,
            new_version: serverVersion,
          },
        });
      }

      // Salvar nova versão em cache
      this._saveCache(cacheKey, {
        data: serverPlaylist,
        version: serverVersion,
        timestamp: Date.now(),
      });

      return serverPlaylist;
    } catch (error) {
      console.error('[PlaylistCacheManager] Error getting playlist:', error);

      // Tentar usar cache mesmo que expirado (fallback)
      const cacheKey = `${CACHE_PREFIX}playlist_${playlistId}`;
      const cached = this._loadCache(cacheKey);
      if (cached) {
        console.warn('[PlaylistCacheManager] Using stale cache due to server error');
        return cached.data;
      }

      throw error;
    }
  }

  /**
   * Invalidar cache de campanha
   */
  invalidateCampaignCache(campaignId) {
    const cacheKey = `${CACHE_PREFIX}campaign_${campaignId}`;
    localStorage.removeItem(cacheKey);
    console.log('[PlaylistCacheManager] Invalidated campaign cache:', campaignId);
  }

  /**
   * Invalidar cache de playlist
   */
  invalidatePlaylistCache(playlistId) {
    const cacheKey = `${CACHE_PREFIX}playlist_${playlistId}`;
    localStorage.removeItem(cacheKey);
    console.log('[PlaylistCacheManager] Invalidated playlist cache:', playlistId);
  }

  /**
   * Limpar todo o cache do player
   * Usado quando usuário clica "Limpar cache" no gerenciador
   */
  clearAllCache() {
    const keys = Object.keys(localStorage);
    let count = 0;

    for (const key of keys) {
      if (key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key);
        count++;
      }
    }

    console.log('[PlaylistCacheManager] Cleared all cache:', count, 'entries');

    logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
      deviceId: this.deviceId,
      details: {
        reason: 'manual_cache_clear',
        entries_cleared: count,
      },
    });

    return count;
  }

  /**
   * Salvar dados em cache (privado)
   */
  _saveCache(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('[PlaylistCacheManager] Error saving cache:', error);
      // Ignorar erro de quota de localStorage
    }
  }

  /**
   * Carregar dados de cache (privado)
   */
  _loadCache(key) {
    try {
      const cached = localStorage.getItem(key);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('[PlaylistCacheManager] Error loading cache:', error);
      // Remover cache corrompido
      localStorage.removeItem(key);
      return null;
    }
  }

  /**
   * Verificar se cache expirou (privado)
   */
  _isCacheExpired(cached) {
    if (!cached || !cached.timestamp) return true;
    const ageMinutes = (Date.now() - cached.timestamp) / (1000 * 60);
    return ageMinutes > CACHE_TTL_MINUTES;
  }

  /**
   * Obter estatísticas de cache
   */
  getCacheStats() {
    const keys = Object.keys(localStorage);
    const cacheEntries = keys.filter(k => k.startsWith(CACHE_PREFIX));

    let totalSize = 0;
    const entries = [];

    for (const key of cacheEntries) {
      const cached = this._loadCache(key);
      if (cached) {
        const size = JSON.stringify(cached).length;
        totalSize += size;
        entries.push({
          key,
          version: cached.version,
          age: Date.now() - cached.timestamp,
          size,
        });
      }
    }

    return {
      totalEntries: entries.length,
      totalSizeBytes: totalSize,
      totalSizeKB: (totalSize / 1024).toFixed(2),
      entries,
    };
  }
}

export default PlaylistCacheManager;
