from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, cast, String
from core.models import Media, Tenant
from core.schemas_completos import MediaCreate, MediaUpdate, MediaResponse
from .crud_base import CRUDBase


class CRUDMedia(CRUDBase[Media, MediaCreate, MediaUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[Media]:
        return db.query(Media).filter(Media.tenant_id == tenant_id).all()
    
    def get_by_type(self, db: Session, *, media_type: str) -> List[Media]:
        return db.query(Media).filter(Media.type == media_type).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[Media]:
        return db.query(Media).filter(Media.status == status).all()
    
    def get_by_category(self, db: Session, *, category: str) -> List[Media]:
        return db.query(Media).filter(Media.category.ilike(f"%{category}%")).all()
    
    def get_by_tags(self, db: Session, *, tags: List[str]) -> List[Media]:
        # Busca mídias que contenham qualquer uma das tags
        filters = []
        for tag in tags:
            filters.append(Media.tags.contains([tag]))
        
        if not filters:
            return self.get_multi(db)
        
        return db.query(Media).filter(or_(*filters)).all()
    
    def get_available(self, db: Session) -> List[Media]:
        return db.query(Media).filter(Media.status == "available").all()
    
    def get_processing(self, db: Session) -> List[Media]:
        return db.query(Media).filter(Media.status == "processing").all()
    
    def get_with_error(self, db: Session) -> List[Media]:
        return db.query(Media).filter(Media.status == "error").all()
    
    def get_by_file_size_range(self, db: Session, *, min_size: int = None, max_size: int = None) -> List[Media]:
        query = db.query(Media)
        
        if min_size is not None:
            query = query.filter(Media.file_size >= min_size)
        
        if max_size is not None:
            query = query.filter(Media.file_size <= max_size)
        
        return query.all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[Media]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(Media)
            .filter(
                or_(
                    Media.name.ilike(f"%{query}%"),
                    Media.description.ilike(f"%{query}%"),
                    Media.category.ilike(f"%{query}%"),
                    cast(Media.tags, String).ilike(f"%{query}%"),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update(self, db: Session, *, db_obj: Media, obj_in) -> Media:
        # SPEC 018 — mesmo padrão das SPECs 016/017 (CRUDAudioTrack.update,
        # CRUDAudioPlaylist.update): archived_at acompanha o enum `status`
        # em qualquer caminho de update (PUT genérico ou update_status()).
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            new_status = new_status.value if hasattr(new_status, "value") else new_status
            db_obj.archived_at = datetime.utcnow() if new_status == "archived" else None
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    def update_status(self, db: Session, *, db_obj: Media, status: str) -> Media:
        return self.update(db, db_obj=db_obj, obj_in={"status": status})

    def get_in_use_references(self, db: Session, *, media_id: str) -> dict:
        """Retorna onde a midia esta em uso, para bloquear exclusao
        definitiva com mensagem clara. Diferente da checagem legada
        (_campaigns_using_media em api/v1/media.py, que so olha os campos
        JSON Campaign.media_ids/media_order), esta tambem conta a tabela
        relacional CampaignPlaylistItem (FK RESTRICT, e o caminho real que o
        player usa para resolver a campanha — ver api/v1/devices.py).
        """
        from core.models import Campaign, CampaignPlaylistItem

        playlist_item_count = (
            db.query(CampaignPlaylistItem)
            .filter(CampaignPlaylistItem.media_id == media_id)
            .count()
        )

        legacy_campaigns = db.query(Campaign).filter(
            (Campaign.media_ids.isnot(None)) | (Campaign.media_order.isnot(None))
        ).all()
        legacy_count = 0
        for campaign in legacy_campaigns:
            media_ids = {str(item) for item in (campaign.media_ids or []) if item}
            if campaign.media_order:
                media_ids.update(
                    str(item.get("media_id"))
                    for item in campaign.media_order
                    if isinstance(item, dict) and item.get("media_id")
                )
            if str(media_id) in media_ids:
                legacy_count += 1

        return {
            "campaign_playlist_items": playlist_item_count,
            "legacy_campaigns": legacy_count,
            "in_use": (playlist_item_count + legacy_count) > 0,
        }
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(Media)
        if tenant_id:
            query = query.filter(Media.tenant_id == tenant_id)
        
        total = query.count()
        available = query.filter(Media.status == "available").count()
        processing = query.filter(Media.status == "processing").count()
        error = query.filter(Media.status == "error").count()
        
        # Estatísticas por tipo
        image_count = query.filter(Media.type == "image").count()
        video_count = query.filter(Media.type == "video").count()
        audio_count = query.filter(Media.type == "audio").count()
        external_count = query.filter(Media.type == "external_url").count()
        
        return {
            "total": total,
            "available": available,
            "processing": processing,
            "error": error,
            "by_type": {
                "image": image_count,
                "video": video_count,
                "audio": audio_count,
                "external_url": external_count
            }
        }


# Instância única do CRUD
crud_media = CRUDMedia(Media)
