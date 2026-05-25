import json
import unittest
from enum import Enum
from pathlib import Path
from unittest.mock import Mock, patch

from tasks.media.backfill_has_audio import detect_audio_streams, local_media_path, media_type_value


class MediaType(str, Enum):
    VIDEO = "video"


class AudioBackfillTest(unittest.TestCase):
    def test_media_type_value_accepts_enum_and_string(self):
        self.assertEqual(media_type_value(MediaType.VIDEO), "video")
        self.assertEqual(media_type_value("VIDEO"), "video")
        self.assertEqual(media_type_value(None), "")

    def test_local_media_path_ignores_remote_or_empty_urls(self):
        self.assertIsNone(local_media_path(None))
        self.assertIsNone(local_media_path("https://cdn.example/video.mp4"))

    def test_local_media_path_resolves_upload_url_from_root(self):
        self.assertEqual(
            local_media_path("/uploads/media/video.mp4", root=Path("/app")),
            Path("/app/uploads/media/video.mp4"),
        )

    @patch("tasks.media.backfill_has_audio.subprocess.run")
    def test_detect_audio_streams_returns_true_when_ffprobe_finds_audio(self, run):
        run.return_value = Mock(stdout=json.dumps({"streams": [{"codec_type": "audio"}]}))

        self.assertTrue(detect_audio_streams(Path("/tmp/video.mp4")))

    @patch("tasks.media.backfill_has_audio.subprocess.run")
    def test_detect_audio_streams_returns_false_without_audio_streams(self, run):
        run.return_value = Mock(stdout=json.dumps({"streams": []}))

        self.assertFalse(detect_audio_streams(Path("/tmp/video.mp4")))

    @patch("tasks.media.backfill_has_audio.subprocess.run", side_effect=FileNotFoundError)
    def test_detect_audio_streams_returns_none_when_ffprobe_is_unavailable(self, _run):
        self.assertIsNone(detect_audio_streams(Path("/tmp/video.mp4")))


if __name__ == "__main__":
    unittest.main()
