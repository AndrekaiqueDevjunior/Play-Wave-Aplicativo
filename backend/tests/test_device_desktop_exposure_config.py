import unittest
import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from api.v1.devices import (
    DeviceDesktopExposureConfigUpdate,
    _build_player_playlist_response,
    update_device_desktop_exposure_config,
)
from core.models import Device


class TestDeviceDesktopExposureConfig(unittest.TestCase):
    def test_update_desktop_exposure_config_enabled_requires_interval_and_duration(self):
        device = Device(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="TV Store",
            pairing_code="PAIR-001",
            status="online",
            device_token="device-token",
            is_active=True,
            is_blocked=False,
            requires_repairing=False,
            audio_volume=0.7,
        )
        user = SimpleNamespace(role="admin", tenant_id=device.tenant_id)
        body = DeviceDesktopExposureConfigUpdate(enabled=True)

        with patch("api.v1.devices.crud_device.get", return_value=device):
            with self.assertRaises(HTTPException) as ctx:
                update_device_desktop_exposure_config(
                    db=MagicMock(),
                    current_user=user,
                    device_id=str(device.id),
                    body=body,
                )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("interval_seconds and duration_seconds", str(ctx.exception.detail))

    def test_build_player_playlist_response_includes_desktop_exposure_config(self):
        device = Device(
            id=uuid.uuid4(),
            tenant_id=None,
            name="TV Store",
            pairing_code="PAIR-002",
            status="online",
            device_token="device-token",
            is_active=True,
            is_blocked=False,
            requires_repairing=False,
            audio_volume=0.7,
            desktop_exposure_enabled=True,
            desktop_exposure_interval_seconds=20,
            desktop_exposure_duration_seconds=5,
            desktop_exposure_restore_fullscreen=False,
            desktop_exposure_updated_at=datetime(2026, 6, 1, 0, 0, 0),
        )

        db = MagicMock()
        with patch("api.v1.devices._resolve_player_campaign", return_value=None), \
             patch("api.v1.devices._build_audio_playlist", return_value=None), \
             patch("services.osd_config_resolver.resolve_osd_config", return_value={}):
            result = _build_player_playlist_response(db, device=device)

        self.assertIn("desktop_exposure_config", result)
        desktop_config = result["desktop_exposure_config"]
        self.assertTrue(desktop_config["enabled"])
        self.assertEqual(desktop_config["interval_seconds"], 20)
        self.assertEqual(desktop_config["duration_seconds"], 5)
        self.assertFalse(desktop_config["restore_fullscreen"])
        self.assertEqual(desktop_config["updated_at"], datetime(2026, 6, 1, 0, 0, 0))

    def test_desktop_exposure_config_rejects_out_of_range_interval(self):
        with self.assertRaises(ValidationError):
            DeviceDesktopExposureConfigUpdate(
                enabled=True,
                interval_seconds=5,
                duration_seconds=5,
            )

    def test_desktop_exposure_config_defaults_disabled_for_old_device(self):
        device = Device(
            id=uuid.uuid4(),
            tenant_id=None,
            name="TV Store",
            pairing_code="PAIR-003",
            status="online",
            device_token="device-token",
            is_active=True,
            is_blocked=False,
            requires_repairing=False,
            audio_volume=0.7,
        )

        self.assertFalse(device.desktop_exposure_config["enabled"])
        self.assertIsNone(device.desktop_exposure_config["interval_seconds"])
        self.assertIsNone(device.desktop_exposure_config["duration_seconds"])
        self.assertTrue(device.desktop_exposure_config["restore_fullscreen"])
        self.assertIsNone(device.desktop_exposure_config["updated_at"])
        # SPEC 015 — aviso desabilitado por padrão em devices antigos.
        self.assertFalse(device.desktop_exposure_config["show_warning"])
        self.assertIsNone(device.desktop_exposure_config["warning_seconds_before"])
        self.assertIsNone(device.desktop_exposure_config["warning_text"])
        self.assertIsNone(device.desktop_exposure_config["warning_media_id"])

    def test_desktop_exposure_config_exposes_warning_fields_when_set(self):
        media_id = uuid.uuid4()
        device = Device(
            id=uuid.uuid4(),
            tenant_id=None,
            name="TV Store",
            pairing_code="PAIR-004",
            status="online",
            device_token="device-token",
            is_active=True,
            is_blocked=False,
            requires_repairing=False,
            audio_volume=0.7,
            desktop_exposure_enabled=True,
            desktop_exposure_interval_seconds=600,
            desktop_exposure_duration_seconds=30,
            desktop_exposure_show_warning=True,
            desktop_exposure_warning_seconds_before=15,
            desktop_exposure_warning_text="Voltamos já",
            desktop_exposure_warning_media_id=media_id,
        )

        config = device.desktop_exposure_config
        self.assertTrue(config["show_warning"])
        self.assertEqual(config["warning_seconds_before"], 15)
        self.assertEqual(config["warning_text"], "Voltamos já")
        self.assertEqual(config["warning_media_id"], str(media_id))

    def test_update_desktop_exposure_config_persists_warning_fields(self):
        device = Device(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="TV Store",
            pairing_code="PAIR-005",
            status="online",
            device_token="device-token",
            is_active=True,
            is_blocked=False,
            requires_repairing=False,
            audio_volume=0.7,
        )
        user = SimpleNamespace(role="admin", tenant_id=device.tenant_id)
        body = DeviceDesktopExposureConfigUpdate(
            show_warning=True,
            warning_seconds_before=20,
            warning_text="Aviso de minimização",
        )

        with patch("api.v1.devices.crud_device.get", return_value=device), \
             patch("api.v1.devices._invalidate_device_playlist_cache"), \
             patch("api.v1.devices._publish_device_playlist_invalidated"):
            result = update_device_desktop_exposure_config(
                db=MagicMock(),
                current_user=user,
                device_id=str(device.id),
                body=body,
            )

        self.assertTrue(device.desktop_exposure_show_warning)
        self.assertEqual(device.desktop_exposure_warning_seconds_before, 20)
        self.assertEqual(device.desktop_exposure_warning_text, "Aviso de minimização")
        self.assertTrue(result["desktop_exposure_config"]["show_warning"])

    def test_desktop_exposure_warning_seconds_before_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            DeviceDesktopExposureConfigUpdate(
                show_warning=True,
                warning_seconds_before=121,
            )
