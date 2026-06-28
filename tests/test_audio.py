import sys
import os
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import Track, fetch_tracks, YTDL_OPTIONS, FFMPEG_OPTIONS


class TestTrack:
    def test_basic_initialization(self):
        data = {
            "title": "My Song",
            "url": "http://stream.example.com/audio.mp3",
            "webpage_url": "http://example.com/watch?v=123",
            "duration": 240,
            "thumbnail": "http://example.com/thumb.jpg",
            "uploader": "Test Artist",
        }
        t = Track(data)
        assert t.title == "My Song"
        assert t.stream_url == "http://stream.example.com/audio.mp3"
        assert t.webpage_url == "http://example.com/watch?v=123"
        assert t.duration == 240
        assert t.thumbnail == "http://example.com/thumb.jpg"
        assert t.uploader == "Test Artist"

    def test_missing_title_defaults_to_unknown(self):
        t = Track({"url": "http://stream.url"})
        assert t.title == "Unknown"

    def test_empty_title_defaults_to_unknown(self):
        t = Track({"title": "", "url": "http://stream.url"})
        assert t.title == "Unknown"

    def test_missing_url_raises(self):
        # A track with no stream URL cannot be played, so Track rejects it.
        with pytest.raises(ValueError):
            Track({"title": "No URL"})

    def test_webpage_url_falls_back_to_stream_url(self):
        t = Track({"title": "Fallback", "url": "http://stream.url"})
        assert t.webpage_url == "http://stream.url"

    def test_missing_optional_fields(self):
        t = Track({"title": "Minimal", "url": "http://s.url"})
        assert t.duration is None
        assert t.thumbnail is None
        assert t.uploader == ""

    def test_repr(self):
        t = Track({"title": "Repr Test", "url": "http://s.url"})
        assert repr(t) == "<Track title='Repr Test'>"

    def test_repr_with_special_chars(self):
        t = Track({"title": "It's a \"Test\"", "url": "http://s.url"})
        r = repr(t)
        assert r.startswith("<Track title=")
        assert r.endswith(">")
        assert "Test" in r


class TestFetchTracks:
    @pytest.mark.asyncio
    async def test_single_track_result(self):
        mock_data = {
            "title": "Single Song",
            "url": "http://stream.url/single",
            "webpage_url": "http://example.com/single",
            "duration": 180,
            "thumbnail": None,
            "uploader": "Artist",
        }

        with patch("audio.yt_dlp.YoutubeDL") as mock_ytdl_cls:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_data
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdl_cls.return_value = mock_instance

            tracks = await fetch_tracks("test query")

        assert len(tracks) == 1
        assert tracks[0].title == "Single Song"
        assert tracks[0].stream_url == "http://stream.url/single"

    @pytest.mark.asyncio
    async def test_playlist_result(self):
        mock_data = {
            "entries": [
                {"title": "Song 1", "url": "http://stream/1"},
                {"title": "Song 2", "url": "http://stream/2"},
                {"title": "Song 3", "url": "http://stream/3"},
            ]
        }

        with patch("audio.yt_dlp.YoutubeDL") as mock_ytdl_cls:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_data
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdl_cls.return_value = mock_instance

            tracks = await fetch_tracks("playlist url")

        assert len(tracks) == 3
        assert tracks[0].title == "Song 1"
        assert tracks[2].title == "Song 3"

    @pytest.mark.asyncio
    async def test_playlist_skips_entries_without_url(self):
        mock_data = {
            "entries": [
                {"title": "Good", "url": "http://stream/good"},
                {"title": "No URL"},
                None,
                {"title": "Also Good", "url": "http://stream/also"},
            ]
        }

        with patch("audio.yt_dlp.YoutubeDL") as mock_ytdl_cls:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_data
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdl_cls.return_value = mock_instance

            tracks = await fetch_tracks("mixed playlist")

        assert len(tracks) == 2
        assert tracks[0].title == "Good"
        assert tracks[1].title == "Also Good"

    @pytest.mark.asyncio
    async def test_no_results_raises_value_error(self):
        with patch("audio.yt_dlp.YoutubeDL") as mock_ytdl_cls:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = None
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdl_cls.return_value = mock_instance

            with pytest.raises(ValueError, match="No results found"):
                await fetch_tracks("nonexistent")

    @pytest.mark.asyncio
    async def test_empty_playlist_raises_value_error(self):
        mock_data = {
            "entries": [
                None,
                {"title": "No URL Entry"},
            ]
        }

        with patch("audio.yt_dlp.YoutubeDL") as mock_ytdl_cls:
            mock_instance = MagicMock()
            mock_instance.extract_info.return_value = mock_data
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_ytdl_cls.return_value = mock_instance

            with pytest.raises(ValueError, match="No playable tracks"):
                await fetch_tracks("empty playlist")


class TestConstants:
    def test_ytdl_options_has_expected_keys(self):
        assert YTDL_OPTIONS["format"] == "bestaudio/best"
        assert YTDL_OPTIONS["noplaylist"] is False
        assert YTDL_OPTIONS["playlistend"] == 50
        assert YTDL_OPTIONS["default_search"] == "ytsearch"
        assert YTDL_OPTIONS["quiet"] is True

    def test_ffmpeg_options_structure(self):
        assert "before_options" in FFMPEG_OPTIONS
        assert "options" in FFMPEG_OPTIONS
        assert "-reconnect" in FFMPEG_OPTIONS["before_options"]
        assert "-vn" in FFMPEG_OPTIONS["options"]
