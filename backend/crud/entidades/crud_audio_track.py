from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import AudioTrack, Tenant
from core.schemas_completos import AudioTrackCreate, AudioTrackUpdate, AudioTrackResponse
from .crud_base import CRUDBase


class CRUDAudioTrack(CRUDBase[AudioTrack, AudioTrackCreate, AudioTrackUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[AudioTrack]:
        return db.query(AudioTrack).filter(AudioTrack.tenant_id == tenant_id).all()
    
    def get_by_category(self, db: Session, *, category: str) -> List[AudioTrack]:
        return db.query(AudioTrack).filter(AudioTrack.category == category).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[AudioTrack]:
        return db.query(AudioTrack).filter(AudioTrack.status == status).all()
    
    def get_active(self, db: Session) -> List[AudioTrack]:
        return db.query(AudioTrack).filter(AudioTrack.status == "active").all()
    
    def get_by_duration_range(self, db: Session, *, min_seconds: int = None, max_seconds: int = None) -> List[AudioTrack]:
        query = db.query(AudioTrack)
        
        if min_seconds is not None:
            query = query.filter(AudioTrack.duration_seconds >= min_seconds)
        
        if max_seconds is not None:
            query = query.filter(AudioTrack.duration_seconds <= max_seconds)
        
        return query.all()
    
    def get_by_file_size_range(self, db: Session, *, min_size: int = None, max_size: int = None) -> List[AudioTrack]:
        query = db.query(AudioTrack)
        
        if min_size is not None:
            query = query.filter(AudioTrack.file_size >= min_size)
        
        if max_size is not None:
            query = query.filter(AudioTrack.file_size <= max_size)
        
        return query.all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[AudioTrack]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(AudioTrack)
            .filter(
                or_(
                    AudioTrack.name.ilike(f"%{query}%"),
                    AudioTrack.description.ilike(f"%{query}%"),
                    AudioTrack.category.ilike(f"%{query}%"),
                    AudioTrack.notes.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update(self, db: Session, *, db_obj: AudioTrack, obj_in) -> AudioTrack:
        # SPEC 016 — archived_at acompanha o enum `status` sempre que ele
        # muda, seja via PUT genérico (fluxo real usado pela UI hoje,
        # `atualizarFaixa`) ou via update_status() abaixo. Setado ao entrar
        # em ARCHIVED, limpo ao saír (restore para active/inactive) — evita
        # que o timestamp fique dessincronizado dependendo de qual endpoint
        # foi usado para arquivar/restaurar.
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            new_status = new_status.value if hasattr(new_status, "value") else new_status
            db_obj.archived_at = datetime.utcnow() if new_status == "archived" else None
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    def update_status(self, db: Session, *, db_obj: AudioTrack, status: str) -> AudioTrack:
        return self.update(db, db_obj=db_obj, obj_in={"status": status})

    def get_in_use_references(self, db: Session, *, track_id: str) -> dict:
        """Retorna onde a faixa esta em uso (playlists, pastas, spots), para
        bloquear exclusao definitiva com uma mensagem clara em vez de deixar
        a constraint RESTRICT do banco estourar um IntegrityError genérico.
        """
        from core.models import AudioPlaylistItem, AudioFolderTrack, AudioSpot

        playlist_count = (
            db.query(AudioPlaylistItem)
            .filter(AudioPlaylistItem.track_id == track_id)
            .count()
        )
        folder_count = (
            db.query(AudioFolderTrack)
            .filter(AudioFolderTrack.track_id == track_id)
            .count()
        )
        spot_count = (
            db.query(AudioSpot)
            .filter(AudioSpot.track_id == track_id)
            .count()
        )
        return {
            "playlists": playlist_count,
            "folders": folder_count,
            "spots": spot_count,
            "in_use": (playlist_count + folder_count + spot_count) > 0,
        }
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(AudioTrack)
        if tenant_id:
            query = query.filter(AudioTrack.tenant_id == tenant_id)
        
        total = query.count()
        active = query.filter(AudioTrack.status == "active").count()
        inactive = query.filter(AudioTrack.status == "inactive").count()
        archived = query.filter(AudioTrack.status == "archived").count()
        
        # Estatísticas por categoria
        music_count = query.filter(AudioTrack.category == "music").count()
        jingle_count = query.filter(AudioTrack.category == "jingle").count()
        announcement_count = query.filter(AudioTrack.category == "announcement").count()
        ambient_count = query.filter(AudioTrack.category == "ambient").count()
        other_count = query.filter(AudioTrack.category == "other").count()
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "archived": archived,
            "by_category": {
                "music": music_count,
                "jingle": jingle_count,
                "announcement": announcement_count,
                "ambient": ambient_count,
                "other": other_count
            }
        }


# Instância única do CRUD
crud_audio_track = CRUDAudioTrack(AudioTrack)
