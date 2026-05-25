from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioPlaylist, AudioPlaylistItem, AudioTrack, AudioTrackStatus, Device, User

router = APIRouter(prefix="/audio/devices", tags=["audio-devices"])


@router.get("/{device_id}/playlist")
def get_device_audio_playlist(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    if not device.audio_playlist_id:
        raise HTTPException(status_code=404, detail="Dispositivo sem playlist de áudio")

    playlist = db.query(AudioPlaylist).filter(
        AudioPlaylist.id == device.audio_playlist_id
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist de áudio não encontrada")

    items = (
        db.query(AudioPlaylistItem)
        .filter(AudioPlaylistItem.playlist_id == playlist.id)
        .order_by(AudioPlaylistItem.order_index, AudioPlaylistItem.created_at)
        .all()
    )
    entries = (
        [(item, str(item.track_id)) for item in items if item.is_active]
        if items
        else [(None, str(tid)) for tid in (playlist.track_ids or []) if tid]
    )

    tracks = []
    if entries:
        track_objs = db.query(AudioTrack).filter(
            AudioTrack.id.in_([track_id for _, track_id in entries]),
            AudioTrack.status == AudioTrackStatus.ACTIVE,
        ).all()
        track_map = {str(t.id): t for t in track_objs}
        for item, track_id in entries:
            t = track_map.get(track_id)
            if t:
                volume = (
                    item.volume_override
                    if item is not None and item.volume_override is not None
                    else (playlist.track_volumes or {}).get(str(t.id), playlist.volume_default)
                )
                tracks.append({
                    "id": str(t.id),
                    "file_url": t.file_url,
                    "name": t.name,
                    "duration_seconds": t.duration_seconds or 0,
                    "volume": volume,
                })

    return {
        "playlist_id": str(playlist.id),
        "tracks": tracks,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
    }
