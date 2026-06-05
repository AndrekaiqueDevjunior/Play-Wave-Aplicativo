from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioFolder, AudioFolderTrack, AudioTrack, User
from core.schemas_completos import (
    AudioFolderCreate,
    AudioFolderResponse,
    AudioFolderStatusEnum,
    AudioFolderTrackBulkCreate,
    AudioFolderTrackReorderPayload,
    AudioFolderTrackResponse,
    AudioFolderTrackUpdate,
    AudioFolderUpdate,
)
from crud.entidades import crud_audio_folder, crud_audio_folder_track


router = APIRouter(prefix="/audio/folders", tags=["audio-folders"])


def _authorize_folder_access(
    db: Session, *, folder_id: str, current_user: User
) -> AudioFolder:
    folder = crud_audio_folder.get(db, id=folder_id)
    if not folder:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Pasta de áudio não encontrada",
        )
    if current_user.role != "admin" and str(folder.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta pasta",
        )
    return folder


def _ensure_track_in_folder_scope(
    db: Session, *, track_id: str, folder: AudioFolder, current_user: User
) -> AudioTrack:
    track = db.query(AudioTrack).filter(AudioTrack.id == track_id).first()
    if not track:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada",
        )
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para usar esta faixa",
        )
    if folder.tenant_id and track.tenant_id and str(track.tenant_id) != str(folder.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Faixa pertence a outro tenant",
        )
    return track


@router.get("/", response_model=List[AudioFolderResponse])
def list_audio_folders(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[AudioFolderStatusEnum] = Query(None),
    category_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
):
    query = db.query(AudioFolder)

    effective_tenant_id = tenant_id
    if current_user.role != "admin":
        effective_tenant_id = str(current_user.tenant_id)

    if effective_tenant_id:
        query = query.filter(AudioFolder.tenant_id == effective_tenant_id)
    if status:
        query = query.filter(AudioFolder.status == status.value)
    if category_id:
        query = query.filter(AudioFolder.category_id == category_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(AudioFolder.name.ilike(like), AudioFolder.description.ilike(like))
        )

    return query.order_by(AudioFolder.name).offset(skip).limit(limit).all()


@router.get("/active/list", response_model=List[AudioFolderResponse])
def list_active_audio_folders(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    query = db.query(AudioFolder).filter(
        AudioFolder.status == AudioFolderStatusEnum.ACTIVE.value,
        AudioFolder.is_active == True,
    )
    if current_user.role != "admin":
        query = query.filter(AudioFolder.tenant_id == str(current_user.tenant_id))
    return query.order_by(AudioFolder.name).offset(skip).limit(limit).all()


@router.get("/{folder_id}", response_model=AudioFolderResponse)
def get_audio_folder(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
):
    return _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )


@router.post("/", response_model=AudioFolderResponse)
def create_audio_folder(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_in: AudioFolderCreate,
):
    if current_user.role != "admin":
        folder_in.tenant_id = str(current_user.tenant_id)
    return crud_audio_folder.create(db, obj_in=folder_in)


@router.put("/{folder_id}", response_model=AudioFolderResponse)
def update_audio_folder(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
    folder_in: AudioFolderUpdate,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    return crud_audio_folder.update(db, db_obj=folder, obj_in=folder_in)


@router.delete("/{folder_id}")
def delete_audio_folder(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
):
    _authorize_folder_access(db, folder_id=folder_id, current_user=current_user)
    crud_audio_folder.remove(db, id=folder_id)
    return {"message": "Pasta de áudio removida com sucesso"}


@router.get("/{folder_id}/tracks", response_model=List[AudioFolderTrackResponse])
def list_audio_folder_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    return crud_audio_folder_track.list_by_folder(db, folder_id=str(folder.id))


@router.post(
    "/{folder_id}/tracks",
    response_model=List[AudioFolderTrackResponse],
    status_code=http_status.HTTP_201_CREATED,
)
def add_audio_folder_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
    payload: AudioFolderTrackBulkCreate,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    next_index = crud_audio_folder_track.next_order_index(db, folder_id=str(folder.id))

    for entry in payload.tracks:
        track = _ensure_track_in_folder_scope(
            db,
            track_id=entry.track_id,
            folder=folder,
            current_user=current_user,
        )
        existing = crud_audio_folder_track.get_by_folder_track(
            db, folder_id=str(folder.id), track_id=str(track.id)
        )
        order_index = entry.order_index if entry.order_index is not None else next_index
        if entry.order_index is None:
            next_index += 10
        if existing:
            existing.order_index = order_index
            existing.volume_override = entry.volume_override
            existing.is_active = entry.is_active if entry.is_active is not None else True
            db.add(existing)
        else:
            db.add(
                AudioFolderTrack(
                    folder_id=folder.id,
                    track_id=track.id,
                    order_index=order_index,
                    volume_override=entry.volume_override,
                    is_active=entry.is_active if entry.is_active is not None else True,
                )
            )

    db.flush()
    crud_audio_folder_track.compact_order(db, folder_id=str(folder.id))
    db.commit()
    return crud_audio_folder_track.list_by_folder(db, folder_id=str(folder.id))


@router.put("/{folder_id}/tracks/{item_id}", response_model=AudioFolderTrackResponse)
def update_audio_folder_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
    item_id: str,
    payload: AudioFolderTrackUpdate,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    item = crud_audio_folder_track.get(db, item_id=item_id)
    if not item or str(item.folder_id) != str(folder.id):
        raise HTTPException(status_code=404, detail="Faixa da pasta não encontrada")

    data = payload.model_dump(exclude_unset=True)
    if "track_id" in data and data["track_id"]:
        track = _ensure_track_in_folder_scope(
            db,
            track_id=data["track_id"],
            folder=folder,
            current_user=current_user,
        )
        duplicate = crud_audio_folder_track.get_by_folder_track(
            db, folder_id=str(folder.id), track_id=str(track.id)
        )
        if duplicate and str(duplicate.id) != str(item.id):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Faixa já existe nesta pasta",
            )
        data["track_id"] = track.id

    for field, value in data.items():
        setattr(item, field, value)
    db.add(item)
    db.flush()
    if "order_index" in data:
        crud_audio_folder_track.compact_order(db, folder_id=str(folder.id))
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{folder_id}/tracks/{item_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def remove_audio_folder_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
    item_id: str,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    item = crud_audio_folder_track.get(db, item_id=item_id)
    if not item or str(item.folder_id) != str(folder.id):
        raise HTTPException(status_code=404, detail="Faixa da pasta não encontrada")

    db.delete(item)
    db.flush()
    crud_audio_folder_track.compact_order(db, folder_id=str(folder.id))
    db.commit()
    return None


@router.patch("/{folder_id}/tracks/reorder", response_model=List[AudioFolderTrackResponse])
def reorder_audio_folder_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    folder_id: str,
    payload: AudioFolderTrackReorderPayload,
):
    folder = _authorize_folder_access(
        db, folder_id=folder_id, current_user=current_user
    )
    items = crud_audio_folder_track.apply_reorder(
        db,
        folder_id=str(folder.id),
        entries=[
            {"item_id": entry.item_id, "order_index": entry.order_index}
            for entry in payload.items
        ],
    )
    db.commit()
    return items
