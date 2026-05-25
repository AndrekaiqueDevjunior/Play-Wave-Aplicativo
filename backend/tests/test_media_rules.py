import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException

from api.v1.media import (
    _default_display_duration,
    _media_availability,
    _parse_datetime_input,
    _validate_period,
)
from core.models import MediaStatus


class MediaRulesTest(unittest.TestCase):
    def test_image_uses_default_display_duration(self):
        self.assertEqual(_default_display_duration("image", None), 15)

    def test_video_uses_natural_duration_by_default(self):
        self.assertIsNone(_default_display_duration("video", None))

    def test_custom_duration_overrides_natural_duration(self):
        self.assertEqual(_default_display_duration("video", 30), 30)

    def test_parse_date_only_as_start_of_day(self):
        self.assertEqual(_parse_datetime_input("2026-05-20"), datetime(2026, 5, 20))

    def test_rejects_end_before_start(self):
        with self.assertRaises(HTTPException):
            _validate_period(datetime(2026, 5, 21), datetime(2026, 5, 20))

    def test_media_availability_statuses(self):
        now = datetime.utcnow()
        base = {
            "status": MediaStatus.AVAILABLE,
            "is_active": True,
            "starts_at": None,
            "ends_at": None,
        }
        self.assertEqual(_media_availability(SimpleNamespace(**base), now=now), "active")
        self.assertEqual(
            _media_availability(SimpleNamespace(**{**base, "starts_at": now + timedelta(days=1)}), now=now),
            "scheduled",
        )
        self.assertEqual(
            _media_availability(SimpleNamespace(**{**base, "ends_at": now - timedelta(days=1)}), now=now),
            "expired",
        )
        self.assertEqual(
            _media_availability(SimpleNamespace(**{**base, "is_active": False}), now=now),
            "inactive",
        )


if __name__ == "__main__":
    unittest.main()
