import sys
import os
from unittest.mock import MagicMock, AsyncMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    format_duration,
    is_script_url_configured,
    require_playing_or_paused,
    require_voice_client,
    ensure_voice_connection,
)


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "0:00"

    def test_under_a_minute_pads_seconds(self):
        assert format_duration(5) == "0:05"

    def test_minutes_and_seconds(self):
        assert format_duration(65) == "1:05"

    def test_large_value_stays_in_minutes(self):
        assert format_duration(3661) == "61:01"

    def test_truncates_float(self):
        assert format_duration(90.9) == "1:30"


class TestIsScriptUrlConfigured:
    def test_empty_is_false(self):
        assert is_script_url_configured("") is False

    def test_placeholder_is_false(self):
        assert is_script_url_configured("https://script.google.com/YOUR_SCRIPT_URL") is False

    def test_real_url_is_true(self):
        assert is_script_url_configured("https://script.google.com/macros/s/abc/exec") is True


class TestRequirePlayingOrPaused:
    def test_none_vc_is_false(self):
        assert require_playing_or_paused(None) is False

    def test_playing_is_true(self):
        vc = MagicMock()
        vc.is_playing.return_value = True
        vc.is_paused.return_value = False
        assert require_playing_or_paused(vc) is True

    def test_idle_is_false(self):
        vc = MagicMock()
        vc.is_playing.return_value = False
        vc.is_paused.return_value = False
        assert require_playing_or_paused(vc) is False


def _interaction(voice_client=None, user_in_voice=True, channel=None):
    """Build a mock discord.Interaction with async response.send_message."""
    interaction = MagicMock()
    interaction.guild.voice_client = voice_client
    interaction.response.send_message = AsyncMock()
    if user_in_voice:
        interaction.user.voice.channel = channel or MagicMock(name="user_channel")
    else:
        interaction.user.voice = None
    return interaction


class TestRequireVoiceClient:
    async def test_not_connected_sends_error_and_returns_none(self):
        interaction = _interaction(voice_client=None)
        result = await require_voice_client(interaction)
        assert result is None
        interaction.response.send_message.assert_awaited_once()

    async def test_playing_required_but_idle_returns_none(self):
        vc = MagicMock()
        vc.is_playing.return_value = False
        interaction = _interaction(voice_client=vc)
        result = await require_voice_client(interaction, playing=True)
        assert result is None

    async def test_connected_returns_vc(self):
        vc = MagicMock()
        vc.is_playing.return_value = True
        interaction = _interaction(voice_client=vc)
        result = await require_voice_client(interaction, playing=True)
        assert result is vc


class TestEnsureVoiceConnection:
    async def test_user_not_in_voice_returns_none(self):
        interaction = _interaction(voice_client=None, user_in_voice=False)
        assert await ensure_voice_connection(interaction) is None

    async def test_connects_when_not_in_a_channel(self):
        user_channel = MagicMock(name="user_channel")
        vc = MagicMock(name="vc")
        user_channel.connect = AsyncMock(return_value=vc)
        interaction = _interaction(voice_client=None, channel=user_channel)
        result = await ensure_voice_connection(interaction)
        assert result is vc
        user_channel.connect.assert_awaited_once()

    async def test_moves_when_in_a_different_channel(self):
        user_channel = MagicMock(name="user_channel")
        vc = MagicMock(name="vc")
        vc.channel = MagicMock(name="other_channel")  # different object
        vc.move_to = AsyncMock()
        interaction = _interaction(voice_client=vc, channel=user_channel)
        result = await ensure_voice_connection(interaction)
        assert result is vc
        vc.move_to.assert_awaited_once_with(user_channel)

    async def test_no_move_when_already_in_channel(self):
        user_channel = MagicMock(name="user_channel")
        vc = MagicMock(name="vc")
        vc.channel = user_channel  # same object
        vc.move_to = AsyncMock()
        interaction = _interaction(voice_client=vc, channel=user_channel)
        result = await ensure_voice_connection(interaction)
        assert result is vc
        vc.move_to.assert_not_called()
