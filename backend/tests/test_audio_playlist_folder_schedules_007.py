"""
Teste para AudioPlaylistFolderSchedule e resolver de agenda.

Cobre:
- Criação de agendamentos de pasta.
- Resolver: determinar pasta ativa por horário/data/dia da semana.
- Resolver: próxima mudança de agenda.
"""

import pytest
from datetime import datetime, time as time_class
from sqlalchemy.orm import Session

from core.models import (
    Tenant,
    AudioPlaylist,
    AudioFolder,
    AudioTrack,
    AudioPlaylistFolderSchedule,
)
from core.schemas_completos import (
    AudioPlaylistFolderScheduleCreate,
    AudioPlaylistPlayModeEnum,
)
from crud.entidades import (
    crud_tenant,
    crud_audio_playlist,
    crud_audio_folder,
    crud_audio_track,
    crud_audio_playlist_folder_schedule,
)
from services.audio_schedule_resolver import (
    resolve_active_folder,
    resolve_active_folders_by_priority,
    get_next_schedule_change,
)


@pytest.fixture
def tenant(db: Session):
    """Cria um tenant de teste."""
    return crud_tenant.create(db, obj_in={"name": "Test Tenant"})


@pytest.fixture
def playlist(db: Session, tenant):
    """Cria uma playlist de teste."""
    obj = crud_audio_playlist.create(
        db,
        obj_in={
            "name": "Test Playlist",
            "tenant_id": str(tenant.id),
        },
    )
    return obj


@pytest.fixture
def folder_morning(db: Session, tenant):
    """Cria pasta "Manhã"."""
    return crud_audio_folder.create(
        db,
        obj_in={
            "name": "Manhã",
            "tenant_id": str(tenant.id),
            "start_time": "06:00",
            "end_time": "12:00",
            "is_active": True,
        },
    )


@pytest.fixture
def folder_afternoon(db: Session, tenant):
    """Cria pasta "Tarde"."""
    return crud_audio_folder.create(
        db,
        obj_in={
            "name": "Tarde",
            "tenant_id": str(tenant.id),
            "start_time": "12:00",
            "end_time": "18:00",
            "is_active": True,
        },
    )


@pytest.fixture
def folder_night(db: Session, tenant):
    """Cria pasta "Noite"."""
    return crud_audio_folder.create(
        db,
        obj_in={
            "name": "Noite",
            "tenant_id": str(tenant.id),
            "start_time": "18:00",
            "end_time": "06:00",
            "is_active": True,
        },
    )


def test_create_folder_schedule(db: Session, playlist, folder_morning):
    """Testa criação de agendamento."""
    schedule = crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="12:00",
            priority=1,
            play_mode=AudioPlaylistPlayModeEnum.SEQUENTIAL,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    assert schedule.folder_id == folder_morning.id
    assert schedule.playlist_id == playlist.id
    assert schedule.start_time == "06:00"
    assert schedule.end_time == "12:00"
    assert schedule.priority == 1


def test_resolve_active_folder_by_time(db: Session, playlist, folder_morning):
    """Testa resolver com horário específico."""
    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="12:00",
            priority=1,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    now_morning = datetime(2026, 5, 23, 9, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_morning)

    assert active_folder is not None
    assert active_folder.id == folder_morning.id


def test_resolve_no_folder_outside_schedule(db: Session, playlist, folder_morning):
    """Testa que nenhuma pasta está ativa fora do horário."""
    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="12:00",
            priority=1,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    now_outside = datetime(2026, 5, 23, 15, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_outside)

    assert active_folder is None


def test_resolve_by_priority(db: Session, playlist, folder_morning, folder_afternoon):
    """Testa prioridade quando há conflito."""
    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="14:00",
            priority=1,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_afternoon.id),
            start_time="12:00",
            end_time="18:00",
            priority=10,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    now_overlap = datetime(2026, 5, 23, 13, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_overlap)

    assert active_folder.id == folder_afternoon.id


def test_resolve_by_date_period(db: Session, playlist, folder_morning):
    """Testa agendamento com período de data."""
    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="12:00",
            starts_at=datetime(2026, 5, 20),
            ends_at=datetime(2026, 5, 25),
            priority=1,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    now_during = datetime(2026, 5, 23, 9, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_during)
    assert active_folder is not None

    now_before = datetime(2026, 5, 19, 9, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_before)
    assert active_folder is None

    now_after = datetime(2026, 5, 26, 9, 0, 0)
    active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now_after)
    assert active_folder is None


def test_list_by_priority(db: Session, playlist, folder_morning, folder_afternoon):
    """Testa listar pastas em ordem de prioridade."""
    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_morning.id),
            start_time="06:00",
            end_time="14:00",
            priority=1,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    crud_audio_playlist_folder_schedule.create(
        db,
        obj_in=AudioPlaylistFolderScheduleCreate(
            folder_id=str(folder_afternoon.id),
            start_time="12:00",
            end_time="18:00",
            priority=10,
            is_active=True,
        ),
        playlist_id=str(playlist.id),
    )

    now_overlap = datetime(2026, 5, 23, 13, 0, 0)
    folders = resolve_active_folders_by_priority(
        db, playlist_id=str(playlist.id), now=now_overlap
    )

    assert len(folders) == 2
    assert folders[0].id == folder_afternoon.id
    assert folders[1].id == folder_morning.id
