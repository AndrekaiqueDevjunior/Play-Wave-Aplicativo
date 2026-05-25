import unittest
from enum import Enum
from types import SimpleNamespace

from services.audio_policy_resolver import (
    AUTO,
    MEDIA_AUDIO_ONLY,
    MIX,
    MUTED_VIDEO_WITH_RADIO,
    RADIO_ONLY,
    resolve_campaign_audio_payload,
    resolve_effective_audio_policy,
    resolve_has_audio,
    resolve_media_payload,
)


class AudioPolicyEnum(str, Enum):
    MIX = MIX
    RADIO_ONLY = RADIO_ONLY


class MediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"


class AudioPolicyResolverTest(unittest.TestCase):
    def test_resolves_first_policy_by_hierarchy(self):
        self.assertEqual(
            resolve_effective_audio_policy(
                media_policy=MEDIA_AUDIO_ONLY,
                campaign_policy=RADIO_ONLY,
                device_policy=MIX,
                tenant_policy=MUTED_VIDEO_WITH_RADIO,
            ),
            MEDIA_AUDIO_ONLY,
        )
        self.assertEqual(
            resolve_effective_audio_policy(None, RADIO_ONLY, MIX, AUTO),
            RADIO_ONLY,
        )
        self.assertEqual(
            resolve_effective_audio_policy(None, None, MUTED_VIDEO_WITH_RADIO, AUTO),
            MUTED_VIDEO_WITH_RADIO,
        )
        self.assertEqual(resolve_effective_audio_policy(None, None, None, MIX), MIX)

    def test_defaults_to_auto_when_everything_is_empty(self):
        self.assertEqual(resolve_effective_audio_policy(None, None, None, None), AUTO)
        self.assertEqual(resolve_effective_audio_policy("", None, None, None), AUTO)

    def test_accepts_enum_values(self):
        self.assertEqual(
            resolve_effective_audio_policy(AudioPolicyEnum.MIX, None, None, None),
            MIX,
        )

    def test_resolve_has_audio_uses_explicit_value_first(self):
        self.assertTrue(resolve_has_audio(SimpleNamespace(has_audio=True, type=MediaType.IMAGE)))
        self.assertFalse(resolve_has_audio(SimpleNamespace(has_audio=False, type=MediaType.VIDEO)))

    def test_resolve_has_audio_falls_back_to_video_type(self):
        self.assertTrue(resolve_has_audio(SimpleNamespace(has_audio=None, type=MediaType.VIDEO)))
        self.assertFalse(resolve_has_audio(SimpleNamespace(has_audio=None, type=MediaType.IMAGE)))
        self.assertFalse(resolve_has_audio(SimpleNamespace(has_audio=None, type="external_url")))

    def test_media_payload_includes_effective_policy_and_audio_flag(self):
        payload = resolve_media_payload(
            media=SimpleNamespace(audio_policy=None, has_audio=None, type=MediaType.VIDEO),
            campaign=SimpleNamespace(audio_policy=RADIO_ONLY),
            device=SimpleNamespace(audio_policy_default=MIX),
            tenant=SimpleNamespace(audio_policy_default=AUTO),
        )

        self.assertEqual(payload["audio_policy_effective"], RADIO_ONLY)
        self.assertTrue(payload["has_audio"])

    def test_campaign_payload_uses_campaign_device_tenant_hierarchy_and_default_fade(self):
        payload = resolve_campaign_audio_payload(
            campaign=SimpleNamespace(audio_policy=None),
            device=SimpleNamespace(audio_policy_default=MUTED_VIDEO_WITH_RADIO),
            tenant=SimpleNamespace(audio_policy_default=AUTO, audio_fade_ms=None),
        )

        self.assertEqual(payload["audio_policy_default"], MUTED_VIDEO_WITH_RADIO)
        self.assertEqual(payload["audio_fade_ms"], 200)

    def test_campaign_payload_preserves_tenant_fade(self):
        payload = resolve_campaign_audio_payload(
            campaign=SimpleNamespace(audio_policy=MIX),
            device=SimpleNamespace(audio_policy_default=RADIO_ONLY),
            tenant=SimpleNamespace(audio_policy_default=AUTO, audio_fade_ms=350),
        )

        self.assertEqual(payload["audio_policy_default"], MIX)
        self.assertEqual(payload["audio_fade_ms"], 350)


if __name__ == "__main__":
    unittest.main()
