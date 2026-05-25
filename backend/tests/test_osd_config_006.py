import unittest
from enum import Enum
from types import SimpleNamespace

from services.osd_config_resolver import DEFAULT_OSD_CONFIG, resolve_osd_config, resolve_osd_local


class Position(str, Enum):
    TOP_LEFT = "top_left"
    BOTTOM_LEFT = "bottom_left"


class FontSize(str, Enum):
    SMALL = "small"
    LARGE = "large"


class OSDConfigResolverTest(unittest.TestCase):
    def test_resolves_defaults_without_device_or_tenant(self):
        self.assertEqual(resolve_osd_config(), DEFAULT_OSD_CONFIG)

    def test_tenant_overrides_defaults(self):
        tenant = SimpleNamespace(
            osd_show_current_audio=False,
            osd_position=Position.TOP_LEFT,
            osd_duration_seconds=5,
            osd_opacity=0.75,
            osd_font_size=FontSize.LARGE,
        )

        self.assertEqual(
            resolve_osd_config(tenant=tenant),
            {
                "show_current_audio": False,
                "position": "top_left",
                "duration_seconds": 5,
                "opacity": 0.75,
                "font_size": "large",
            },
        )

    def test_device_overrides_tenant_per_field(self):
        tenant = SimpleNamespace(
            osd_show_current_audio=True,
            osd_position="top_right",
            osd_duration_seconds=8,
            osd_opacity=0.6,
            osd_font_size="medium",
        )
        device = SimpleNamespace(
            osd_show_current_audio=None,
            osd_position=Position.BOTTOM_LEFT,
            osd_duration_seconds=0,
            osd_opacity=None,
            osd_font_size=FontSize.SMALL,
        )

        self.assertEqual(
            resolve_osd_config(device=device, tenant=tenant),
            {
                "show_current_audio": True,
                "position": "bottom_left",
                "duration_seconds": 0,
                "opacity": 0.6,
                "font_size": "small",
            },
        )

    def test_false_and_zero_are_valid_overrides(self):
        tenant = SimpleNamespace(
            osd_show_current_audio=True,
            osd_position="top_right",
            osd_duration_seconds=8,
            osd_opacity=0.6,
            osd_font_size="medium",
        )
        device = SimpleNamespace(
            osd_show_current_audio=False,
            osd_position=None,
            osd_duration_seconds=0,
            osd_opacity=0,
            osd_font_size=None,
        )

        resolved = resolve_osd_config(device=device, tenant=tenant)

        self.assertFalse(resolved["show_current_audio"])
        self.assertEqual(resolved["duration_seconds"], 0)
        self.assertEqual(resolved["opacity"], 0.0)

    def test_resolve_osd_local_keeps_nulls_for_inherited_fields(self):
        device = SimpleNamespace(
            osd_show_current_audio=None,
            osd_position=Position.BOTTOM_LEFT,
            osd_duration_seconds=None,
            osd_opacity=0.5,
            osd_font_size=None,
        )

        self.assertEqual(
            resolve_osd_local(device),
            {
                "show_current_audio": None,
                "position": "bottom_left",
                "duration_seconds": None,
                "opacity": 0.5,
                "font_size": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
