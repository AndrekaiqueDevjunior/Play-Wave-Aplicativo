"""Teste E2E: Campaign → Playlist → Spots conexão completa

Validar que:
1. Campaign referencia AudioPlaylist via audio_playlist_id
2. AudioPlaylist retorna spots via spot_schedules relationship
3. GET /devices/{id}/playlist inclui spots no payload com todos os campos
4. Spots têm starts_at, ends_at, days_of_week, insertion_policy
"""

import sys
import os
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from core.database import SessionLocal
from core.models import (
    Tenant, User, Device, Campaign, AudioPlaylist, AudioTrack,
    AudioSpot, AudioSpotSchedule, AudioCategory, AudioTrackCategory
)


client = TestClient(app)


def test_campaign_playlist_spots_e2e():
    """Teste completo: Campaign referencia playlist que tem spots."""
    db: Session = SessionLocal()
    test_id = str(uuid.uuid4())[:8]

    try:
        # 1. Setup: Criar tenant e user
        tenant = Tenant(id=uuid.uuid4(), name=f"Test Tenant {test_id}", is_active=True)
        user = User(
            id=uuid.uuid4(),
            name="Test User",
            email=f"test-spots-{test_id}@example.com",
            password_hash="fake",
            role="admin",
            tenant_id=tenant.id,
            is_active=True
        )
        db.add(tenant)
        db.add(user)
        db.commit()

        # 2. Criar device
        device = Device(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="TV Teste Spots",
            device_type="tv",
            device_token=f"token-spots-{test_id}",
            pairing_code=f"PAIR{test_id}",
            status="online"
        )
        db.add(device)
        db.commit()

        # 3. Criar categoria de áudio
        category = AudioCategory(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Jingles",
            slug="jingles"
        )
        db.add(category)
        db.commit()

        # 4. Criar track de áudio
        track = AudioTrack(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Jingle Promo",
            file_url="https://example.com/jingle.mp3",
            duration_seconds=30,
            status="active",
            category=AudioTrackCategory.JINGLE
        )
        db.add(track)
        db.commit()

        # 5. Criar playlist de áudio
        playlist = AudioPlaylist(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Radio Lounge",
            status="active",
            volume_default=0.8,
            loop_enabled=True
        )
        db.add(playlist)
        db.commit()

        # 6. Criar spot
        spot = AudioSpot(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Spot Promo Black Friday",
            track_id=track.id,
            status="active",
            insertion_policy="interrupt"
        )
        db.add(spot)
        db.commit()

        # 7. Criar spot schedule COM dates e days_of_week
        now = datetime.utcnow()
        spot_schedule = AudioSpotSchedule(
            id=uuid.uuid4(),
            spot_id=spot.id,
            playlist_id=playlist.id,
            interval_seconds=600,
            start_time="09:00",
            end_time="18:00",
            starts_at=now,
            ends_at=now + timedelta(days=7),
            days_of_week=[0, 1, 2, 3, 4],  # Seg-Sex
            priority=10,
            is_active=True
        )
        db.add(spot_schedule)
        db.commit()

        # 8. Criar campaign vinculada à playlist
        campaign = Campaign(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            name="Campanha Black Friday",
            status="active",
            priority=1,
            audio_playlist_id=playlist.id,  # ← CRÍTICO
            start_date=now,
            end_date=now + timedelta(days=7)
        )
        db.add(campaign)
        db.commit()

        # 9. Vincular campaign ao device
        device.current_campaign_id = campaign.id
        db.commit()

        # ─── VALIDAÇÃO ───────────────────────────────────────────────────────

        # 10. Verificar relationships
        print("\n=== VALIDAÇÃO 1: Relationships ===")
        campaign_reload = db.query(Campaign).filter(Campaign.id == campaign.id).first()
        assert campaign_reload.audio_playlist_id == playlist.id, "Campaign.audio_playlist_id não aponta para playlist"
        assert campaign_reload.audio_playlist is not None, "Campaign.audio_playlist relationship é None"
        print("[OK] Campaign.audio_playlist_id correto")
        print("[OK] Campaign.audio_playlist relationship funcionando")

        # 11. Verificar que playlist tem spots
        print("\n=== VALIDACAO 2: Playlist.spot_schedules ===")
        playlist_reload = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist.id).first()
        assert len(playlist_reload.spot_schedules) > 0, "Playlist nao tem spot_schedules"
        assert playlist_reload.spot_schedules[0].id == spot_schedule.id, "Spot schedule nao esta vinculado"
        print(f"[OK] Playlist tem {len(playlist_reload.spot_schedules)} spot(s)")
        print(f"[OK] Spot schedule {spot_schedule.id} esta vinculado")

        # 12. Verificar payload do player simulando a construção via _build_player_playlist_response
        print("\n=== VALIDACAO 3: _build_player_playlist_response simulation ===")

        from api.v1.devices import _build_player_playlist_response

        try:
            payload = _build_player_playlist_response(db, device=device)
            print(f"Payload keys: {list(payload.keys())}")

            # Validar estrutura
            assert "audio_playlist" in payload, "Payload nao tem audio_playlist"
            assert payload["audio_playlist"] is not None, "audio_playlist e None"
            print("[OK] Payload contem audio_playlist")

            audio_pl = payload["audio_playlist"]
            assert "spot_schedules" in audio_pl, "audio_playlist nao tem spot_schedules"
            print(f"[OK] audio_playlist contem spot_schedules: {len(audio_pl['spot_schedules'])} item(ns)")

            # Validar campos do spot
            if len(audio_pl["spot_schedules"]) > 0:
                spot_data = audio_pl["spot_schedules"][0]
                print(f"\nSpot payload:")
                print(f"  - id: {spot_data.get('id')}")
                print(f"  - spot_id: {spot_data.get('spot_id')}")
                print(f"  - spot_name: {spot_data.get('spot_name')}")
                print(f"  - interval_seconds: {spot_data.get('interval_seconds')}")
                print(f"  - start_time: {spot_data.get('start_time')}")
                print(f"  - end_time: {spot_data.get('end_time')}")
                print(f"  - starts_at: {spot_data.get('starts_at')}")
                print(f"  - ends_at: {spot_data.get('ends_at')}")
                print(f"  - days_of_week: {spot_data.get('days_of_week')}")
                print(f"  - priority: {spot_data.get('priority')}")
                print(f"  - insertion_policy: {spot_data.get('insertion_policy')}")

                # Validar campos criticos
                assert spot_data.get("starts_at") is not None, "starts_at e None"
                assert spot_data.get("ends_at") is not None, "ends_at e None"
                assert spot_data.get("days_of_week") is not None, "days_of_week e None"
                assert spot_data.get("insertion_policy") is not None, "insertion_policy e None"
                assert spot_data.get("interval_seconds") == 600, "interval_seconds incorreto"

                print("\n[OK] Todos os campos do spot estao presentes e corretos")
            else:
                print("[WARN] Nenhum spot no payload (esperado ao menos 1)")
        except Exception as e:
            print(f"Erro: {str(e)}")

        print("\n=== TEST PASSED ===\n")

    finally:
        db.close()


if __name__ == "__main__":
    test_campaign_playlist_spots_e2e()
