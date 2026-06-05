/**
 * Event Logger — Logs estruturados padronizados para player
 * TASK 35: Padronizar logs da rádio e do player
 */

export const EventType = {
  // Eventos de playlist
  RADIO_PLAYLIST_LOADED: 'radio.playlist.loaded',
  RADIO_FOLDER_RESOLVED: 'radio.folder.resolved',
  RADIO_SCHEDULE_UPDATED: 'radio.schedule.updated',

  // Eventos de track
  RADIO_TRACK_STARTED: 'radio.track.started',
  RADIO_TRACK_ENDED: 'radio.track.ended',
  RADIO_TRACK_FAILED: 'radio.track.failed',
  RADIO_TRACK_SKIPPED: 'radio.track.skipped',

  // Eventos de spot
  RADIO_SPOT_DUE: 'radio.spot.due',
  RADIO_SPOT_STARTED: 'radio.spot.started',
  RADIO_SPOT_FINISHED: 'radio.spot.finished',
  RADIO_SPOT_FAILED: 'radio.spot.failed',

  // Eventos de player
  PLAYER_SCHEDULE_UPDATED: 'player.schedule.updated',
  PLAYER_COMMAND_RECEIVED: 'player.command.received',
  PLAYER_COMMAND_EXECUTED: 'player.command.executed',
  PLAYER_COMMAND_FAILED: 'player.command.failed',
  PLAYER_CACHE_INVALIDATED: 'player.cache.invalidated',

  // Eventos de campanha
  CAMPAIGN_MEDIA_SELECTED: 'campaign.media.selected',
  CAMPAIGN_MEDIA_IGNORED: 'campaign.media.ignored',
  CAMPAIGN_LOADED: 'campaign.loaded',
  CAMPAIGN_UPDATED: 'campaign.updated',
};

/**
 * Log um evento estruturado
 *
 * @param {string} eventType - Tipo de evento (EventType)
 * @param {object} options - Opções do evento
 * @param {string} options.deviceId - ID do dispositivo
 * @param {string} options.playlistId - ID da playlist
 * @param {object} options.details - Detalhes adicionais
 */
export function logEvent(eventType, options = {}) {
  const { deviceId, playlistId, details = {} } = options;

  let msg = `[playwave.events] event=${eventType}`;

  if (deviceId) {
    msg += ` device_id=${deviceId}`;
  }

  if (playlistId) {
    msg += ` playlist_id=${playlistId}`;
  }

  // Adicionar detalhes
  for (const [key, value] of Object.entries(details)) {
    if (typeof value === 'string' && value.includes(' ')) {
      msg += ` ${key}="${value}"`;
    } else {
      msg += ` ${key}=${value}`;
    }
  }

  console.log(msg);
}

/**
 * Log quando playlist é carregada
 */
export function logPlaylistLoaded(deviceId, playlistId, folderCount, trackCount) {
  logEvent(EventType.RADIO_PLAYLIST_LOADED, {
    deviceId,
    playlistId,
    details: {
      folder_count: folderCount,
      track_count: trackCount,
    },
  });
}

/**
 * Log quando track começa a tocar
 */
export function logTrackStarted(deviceId, playlistId, trackId, trackName, durationSeconds) {
  logEvent(EventType.RADIO_TRACK_STARTED, {
    deviceId,
    playlistId,
    details: {
      track_id: trackId,
      track_name: trackName,
      duration_seconds: durationSeconds,
    },
  });
}

/**
 * Log quando track termina
 */
export function logTrackEnded(deviceId, playlistId, trackId, durationSeconds) {
  logEvent(EventType.RADIO_TRACK_ENDED, {
    deviceId,
    playlistId,
    details: {
      track_id: trackId,
      duration_seconds: durationSeconds,
    },
  });
}

/**
 * Log quando track falha
 */
export function logTrackFailed(deviceId, playlistId, trackId, errorReason) {
  logEvent(EventType.RADIO_TRACK_FAILED, {
    deviceId,
    playlistId,
    details: {
      track_id: trackId,
      error_reason: errorReason,
    },
  });
}

/**
 * Log quando spot começa a tocar
 */
export function logSpotStarted(deviceId, playlistId, spotId, spotName) {
  logEvent(EventType.RADIO_SPOT_STARTED, {
    deviceId,
    playlistId,
    details: {
      spot_id: spotId,
      spot_name: spotName,
    },
  });
}

/**
 * Log quando spot termina
 */
export function logSpotFinished(deviceId, playlistId, spotId) {
  logEvent(EventType.RADIO_SPOT_FINISHED, {
    deviceId,
    playlistId,
    details: {
      spot_id: spotId,
    },
  });
}

/**
 * Log quando comando é recebido
 */
export function logCommandReceived(deviceId, commandType, commandId) {
  logEvent(EventType.PLAYER_COMMAND_RECEIVED, {
    deviceId,
    details: {
      command_type: commandType,
      command_id: commandId,
    },
  });
}

/**
 * Log quando comando é executado
 */
export function logCommandExecuted(deviceId, commandType, commandId) {
  logEvent(EventType.PLAYER_COMMAND_EXECUTED, {
    deviceId,
    details: {
      command_type: commandType,
      command_id: commandId,
    },
  });
}

/**
 * Log quando cache é invalidado
 */
export function logCacheInvalidated(deviceId, reason, oldVersion, newVersion) {
  const details = { reason };
  if (oldVersion) details.old_version = oldVersion;
  if (newVersion) details.new_version = newVersion;

  logEvent(EventType.PLAYER_CACHE_INVALIDATED, {
    deviceId,
    details,
  });
}

export default {
  EventType,
  logEvent,
  logPlaylistLoaded,
  logTrackStarted,
  logTrackEnded,
  logTrackFailed,
  logSpotStarted,
  logSpotFinished,
  logCommandReceived,
  logCommandExecuted,
  logCacheInvalidated,
};
