from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioPlaylist, AudioTrack, AudioTrackStatus, Device, User

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

    tracks = []
    if playlist.track_ids:
        track_objs = db.query(AudioTrack).filter(
            AudioTrack.id.in_([str(tid) for tid in playlist.track_ids]),
            AudioTrack.status == AudioTrackStatus.ACTIVE,
        ).all()
        track_map = {str(t.id): t for t in track_objs}
        for tid in playlist.track_ids:
            t = track_map.get(str(tid))
            if t:
                tracks.append({
                    "id": str(t.id),
                    "file_url": t.file_url,
                    "name": t.name,
                    "duration_seconds": t.duration_seconds or 0,
                })

    return {
        "playlist_id": str(playlist.id),
        "tracks": tracks,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
    }
