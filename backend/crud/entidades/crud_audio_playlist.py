from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import AudioPlaylist, AudioTrack, Tenant, Device
from core.schemas_completos import AudioPlaylistCreate, AudioPlaylistUpdate, AudioPlaylistResponse
from .crud_base import CRUDBase


class CRUDAudioPlaylist(CRUDBase[AudioPlaylist, AudioPlaylistCreate, AudioPlaylistUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[AudioPlaylist]:
        return db.query(AudioPlaylist).filter(AudioPlaylist.tenant_id == tenant_id).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[AudioPlaylist]:
        return db.query(AudioPlaylist).filter(AudioPlaylist.status == status).all()
    
    def get_active(self, db: Session) -> List[AudioPlaylist]:
        return db.query(AudioPlaylist).filter(AudioPlaylist.status == "active").all()
    
    def get_with_tracks(self, db: Session, *, playlist_id: str) -> Optional[AudioPlaylist]:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
        if playlist and playlist.track_ids:
            # Carrega as faixas associadas
            tracks = db.query(AudioTrack).filter(AudioTrack.id.in_(playlist.track_ids)).all()
            playlist.tracks = tracks
        return playlist
    
    def get_by_device(self, db: Session, *, device_id: str) -> Optional[AudioPlaylist]:
        device = db.query(Device).filter(Device.id == device_id).first()
        if device and device.audio_playlist_id:
            return db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
        return None
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[AudioPlaylist]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(AudioPlaylist)
            .filter(
                or_(
                    AudioPlaylist.name.ilike(f"%{query}%"),
                    AudioPlaylist.description.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_status(self, db: Session, *, db_obj: AudioPlaylist, status: str) -> AudioPlaylist:
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def add_track(self, db: Session, *, playlist_id: str, track_id: str, volume: float = None) -> AudioPlaylist:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
        if playlist:
            track_ids = [str(tid) for tid in (playlist.track_ids or [])]
            if track_id not in track_ids:
                track_ids.append(track_id)
            playlist.track_ids = track_ids
            
            track_volumes = dict(playlist.track_volumes or {})
            
            if volume is not None:
                track_volumes[track_id] = volume
            playlist.track_volumes = track_volumes
            
            db.add(playlist)
            db.commit()
            db.refresh(playlist)
        return playlist
    
    def remove_track(self, db: Session, *, playlist_id: str, track_id: str) -> AudioPlaylist:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
        if playlist and playlist.track_ids and track_id in playlist.track_ids:
            playlist.track_ids = [tid for tid in playlist.track_ids if str(tid) != str(track_id)]
            track_volumes = dict(playlist.track_volumes or {})
            track_volumes.pop(str(track_id), None)
            playlist.track_volumes = track_volumes
            
            db.add(playlist)
            db.commit()
            db.refresh(playlist)
        return playlist
    
    def reorder_tracks(self, db: Session, *, playlist_id: str, track_ids: List[str]) -> AudioPlaylist:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
        if playlist:
            playlist.track_ids = track_ids
            db.add(playlist)
            db.commit()
            db.refresh(playlist)
        return playlist
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(AudioPlaylist)
        if tenant_id:
            query = query.filter(AudioPlaylist.tenant_id == tenant_id)
        
        total = query.count()
        active = query.filter(AudioPlaylist.status == "active").count()
        inactive = query.filter(AudioPlaylist.status == "inactive").count()
        archived = query.filter(AudioPlaylist.status == "archived").count()
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "archived": archived
        }


# Instância única do CRUD
crud_audio_playlist = CRUDAudioPlaylist(AudioPlaylist)
