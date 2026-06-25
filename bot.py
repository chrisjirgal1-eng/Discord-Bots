import logging
import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv

from audio import fetch_tracks, FFMPEG_OPTIONS
from queue_manager import QueueManager

log = logging.getLogger(__name__)

load_dotenv()

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True


class MusicBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.queues = QueueManager()
        self._voice_locks: dict[int, asyncio.Lock] = {}
        self._reconnecting: set[int] = set()

    def _lock(self, guild_id: int) -> asyncio.Lock:
        if guild_id not in self._voice_locks:
            self._voice_locks[guild_id] = asyncio.Lock()
        return self._voice_locks[guild_id]

    async def setup_hook(self):
        dev_guild_id = os.getenv('DEV_GUILD_ID')
        try:
            if dev_guild_id:
                guild_obj = discord.Object(id=int(dev_guild_id))
                self.tree.copy_global_to(guild=guild_obj)
                await self.tree.sync(guild=guild_obj)
                log.info('Slash commands synced to dev guild %s', dev_guild_id)
            else:
                await self.tree.sync()
                log.info('Slash commands synced globally')
        except discord.HTTPException:
            log.exception('Failed to sync slash commands')

    async def on_ready(self):
        log.info('Logged in as %s (ID: %s)', self.user, self.user.id)
        log.info('Active in %d server(s)', len(self.guilds))
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name='/play')
        )
        for guild in self.guilds:
            await self._auto_join(guild)

    async def _auto_join(self, guild: discord.Guild):
        if guild.voice_client:
            return
        # Join the most populated VC that has at least one human
        best = max(
            (c for c in guild.voice_channels if any(not m.bot for m in c.members)),
            key=lambda c: sum(1 for m in c.members if not m.bot),
            default=None,
        )
        if not best:
            return
        try:
            vc = await best.connect()
            log.info('Auto-joined #%s in %s', best.name, guild.name)
            q = self.queues.get(guild.id)
            if q.current or len(q):
                self.play_next(vc, guild.id)
        except discord.ClientException:
            log.warning('Already connected in %s, skipping auto-join', guild.name)
        except Exception:
            log.exception('Auto-join failed in %s', guild.name)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild

        # Bot itself got disconnected unexpectedly — try to reconnect
        if member.id == self.user.id and before.channel and not after.channel:
            gid = guild.id
            if gid not in self._reconnecting:
                self._reconnecting.add(gid)
                await asyncio.sleep(5)
                self._reconnecting.discard(gid)
                q = self.queues.get(gid)
                if q.current or len(q):
                    await self._auto_join(guild)
            return

        if member.bot:
            return

        vc = guild.voice_client

        # Human joined a VC while bot is not connected anywhere
        if after.channel and after.channel != before.channel and vc is None:
            async with self._lock(guild.id):
                if guild.voice_client is None:
                    try:
                        vc = await after.channel.connect()
                        log.info('Auto-joined #%s in %s', after.channel.name, guild.name)
                        q = self.queues.get(guild.id)
                        if (q.current or len(q)) and not vc.is_playing():
                            self.play_next(vc, guild.id)
                    except discord.ClientException:
                        log.warning('Already connected in %s during member-join auto-join', guild.name)
                    except Exception:
                        log.exception('Auto-join on member join failed in %s', guild.name)

    def play_next(self, vc: discord.VoiceClient, guild_id: int):
        if not vc.is_connected():
            return

        q = self.queues.get(guild_id)
        track = q.next()
        if not track:
            return

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(track.stream_url, **FFMPEG_OPTIONS),
            volume=q.volume,
        )

        def after_cb(error):
            if error:
                log.error('Playback error [%s]: %s', track.title, error)
            fut = asyncio.run_coroutine_threadsafe(self._advance(vc, guild_id), self.loop)
            try:
                fut.result(timeout=10)
            except Exception:
                log.exception('Failed to advance queue after [%s]', track.title)

        try:
            vc.play(source, after=after_cb)
        except Exception:
            log.exception('vc.play failed for [%s], advancing queue', track.title)
            asyncio.run_coroutine_threadsafe(self._advance(vc, guild_id), self.loop)

    async def _advance(self, vc: discord.VoiceClient, guild_id: int):
        try:
            if vc.is_connected():
                self.play_next(vc, guild_id)
        except Exception:
            log.exception('Error advancing playback in guild %s', guild_id)


bot = MusicBot()

# ── /play ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name='play', description='Queue a song or playlist (URL or search query)')
@app_commands.describe(query='YouTube URL, SoundCloud link, or search terms')
async def cmd_play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        await interaction.response.send_message('You need to be in a voice channel.', ephemeral=True)
        return

    await interaction.response.defer()

    guild = interaction.guild
    vc = guild.voice_client
    user_channel = interaction.user.voice.channel

    try:
        if vc is None:
            vc = await user_channel.connect()
        elif vc.channel != user_channel:
            await vc.move_to(user_channel)
    except Exception:
        log.exception('Failed to connect/move to voice channel')
        await interaction.followup.send('Failed to join your voice channel.', ephemeral=True)
        return

    try:
        tracks = await fetch_tracks(query)
    except Exception as e:
        await interaction.followup.send(f'Could not fetch audio: {e}')
        return

    q = bot.queues.get(guild.id)
    q.add_many(tracks)
    was_playing = vc.is_playing() or vc.is_paused()

    if not was_playing:
        bot.play_next(vc, guild.id)

    if len(tracks) == 1:
        verb = 'Now playing' if not was_playing else 'Queued'
        await interaction.followup.send(f'{verb}: **{tracks[0].title}**')
    else:
        msg = f'Queued **{len(tracks)} tracks**'
        if not was_playing and q.current:
            msg += f'\nNow playing: **{q.current.title}**'
        await interaction.followup.send(msg)

# ── /skip ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name='skip', description='Skip the current track')
async def cmd_skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not (vc.is_playing() or vc.is_paused()):
        await interaction.response.send_message('Nothing is playing.', ephemeral=True)
        return
    title = bot.queues.get(interaction.guild.id).current
    vc.stop()
    msg = f'Skipped **{title.title}**.' if title else 'Skipped.'
    await interaction.response.send_message(msg)

# ── /pause / /resume ──────────────────────────────────────────────────────────

@bot.tree.command(name='pause', description='Pause playback')
async def cmd_pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        await interaction.response.send_message('Nothing is playing.', ephemeral=True)
        return
    vc.pause()
    await interaction.response.send_message('Paused.')


@bot.tree.command(name='resume', description='Resume paused playback')
async def cmd_resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_paused():
        await interaction.response.send_message('Not paused.', ephemeral=True)
        return
    vc.resume()
    await interaction.response.send_message('Resumed.')

# ── /nowplaying ───────────────────────────────────────────────────────────────

@bot.tree.command(name='nowplaying', description='Show the currently playing track')
async def cmd_nowplaying(interaction: discord.Interaction):
    q = bot.queues.get(interaction.guild.id)
    if not q.current:
        await interaction.response.send_message('Nothing is playing.', ephemeral=True)
        return
    t = q.current
    embed = discord.Embed(
        title='Now Playing',
        description=f'**[{t.title}]({t.webpage_url})**',
        color=0x1DB954,
    )
    if t.thumbnail:
        embed.set_thumbnail(url=t.thumbnail)
    if t.duration:
        m, s = divmod(int(t.duration), 60)
        embed.add_field(name='Duration', value=f'{m}:{s:02d}', inline=True)
    if t.uploader:
        embed.set_footer(text=f'Uploaded by {t.uploader}')
    await interaction.response.send_message(embed=embed)

# ── /queue ────────────────────────────────────────────────────────────────────

@bot.tree.command(name='queue', description='Show the upcoming queue')
async def cmd_queue(interaction: discord.Interaction):
    q = bot.queues.get(interaction.guild.id)
    upcoming = q.peek()

    if not q.current and not upcoming:
        await interaction.response.send_message('The queue is empty.', ephemeral=True)
        return

    lines = []
    if q.current:
        lines.append(f'**Now playing:** {q.current.title}')
    if upcoming:
        lines.append('')
        lines.append('**Up next:**')
        for i, t in enumerate(upcoming, 1):
            lines.append(f'`{i}.` {t.title}')
    remainder = len(q) - len(upcoming)
    if remainder > 0:
        lines.append(f'*…and {remainder} more*')

    embed = discord.Embed(title='Queue', description='\n'.join(lines), color=0x5865F2)
    await interaction.response.send_message(embed=embed)

# ── /volume ───────────────────────────────────────────────────────────────────

@bot.tree.command(name='volume', description='Set playback volume (0–100)')
@app_commands.describe(level='Volume level from 0 to 100')
async def cmd_volume(interaction: discord.Interaction, level: app_commands.Range[int, 0, 100]):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message('Not connected.', ephemeral=True)
        return
    q = bot.queues.get(interaction.guild.id)
    q.volume = level / 100
    if isinstance(vc.source, discord.PCMVolumeTransformer):
        vc.source.volume = q.volume
    await interaction.response.send_message(f'Volume set to **{level}%**.')

# ── /stop ─────────────────────────────────────────────────────────────────────

@bot.tree.command(name='stop', description='Stop playback and clear the queue')
async def cmd_stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message('Not connected.', ephemeral=True)
        return
    bot.queues.get(interaction.guild.id).clear()
    if vc.is_playing() or vc.is_paused():
        vc.stop()
    await interaction.response.send_message('Stopped and queue cleared.')

# ── /leave ────────────────────────────────────────────────────────────────────

@bot.tree.command(name='leave', description='Disconnect the bot from voice')
async def cmd_leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message('Not in a voice channel.', ephemeral=True)
        return
    bot.queues.get(interaction.guild.id).clear()
    await vc.disconnect()
    await interaction.response.send_message('Disconnected.')


# ── run ───────────────────────────────────────────────────────────────────────

token = os.getenv('DISCORD_TOKEN')
if not token:
    raise RuntimeError('Set DISCORD_TOKEN in your .env file.')

bot.run(token, log_handler=None)
