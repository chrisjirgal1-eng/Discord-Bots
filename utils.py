"""Shared utilities for the Discord music bot.

Consolidates common patterns:
- Voice client precondition checks (require_vc, require_playing, require_paused)
- Guild queue retrieval helpers
"""

from __future__ import annotations

from typing import Optional

import discord


async def require_voice_client(
    interaction: discord.Interaction,
    *,
    playing: bool = False,
    paused: bool = False,
    error_msg: Optional[str] = None,
) -> Optional[discord.VoiceClient]:
    """Return the guild voice client if the precondition is met, else send an
    ephemeral error and return None.

    Parameters
    ----------
    interaction : discord.Interaction
        The slash-command interaction to respond to on failure.
    playing : bool
        If True, also require that the VC is currently playing audio.
    paused : bool
        If True, require that the VC is currently paused.
    error_msg : str | None
        Custom error message; a sensible default is chosen when omitted.
    """
    vc: Optional[discord.VoiceClient] = interaction.guild.voice_client

    if not vc:
        msg = error_msg or "Not connected."
        await interaction.response.send_message(msg, ephemeral=True)
        return None

    if playing and not vc.is_playing():
        msg = error_msg or "Nothing is playing."
        await interaction.response.send_message(msg, ephemeral=True)
        return None

    if paused and not vc.is_paused():
        msg = error_msg or "Not paused."
        await interaction.response.send_message(msg, ephemeral=True)
        return None

    return vc


def require_playing_or_paused(
    vc: Optional[discord.VoiceClient],
) -> bool:
    """Return True if the voice client exists and is either playing or paused."""
    return vc is not None and (vc.is_playing() or vc.is_paused())


async def ensure_voice_connection(
    interaction: discord.Interaction,
) -> Optional[discord.VoiceClient]:
    """Ensure the bot is in the user's voice channel, connecting or moving as
    needed. Returns the VoiceClient, or None if the user isn't in a VC.

    Callers should call ``interaction.response.defer()`` before this if needed.
    """
    guild = interaction.guild
    vc = guild.voice_client
    user_channel = interaction.user.voice.channel if interaction.user.voice else None

    if not user_channel:
        return None

    if vc is None:
        vc = await user_channel.connect()
    elif vc.channel != user_channel:
        await vc.move_to(user_channel)

    return vc


def format_duration(seconds: int) -> str:
    """Format seconds into m:ss display string."""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def is_script_url_configured(url: str) -> bool:
    """Check if a Google Apps Script URL is properly configured (not placeholder)."""
    return bool(url) and "YOUR_" not in url
