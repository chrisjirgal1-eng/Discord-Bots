import asyncio
import logging
import os

import yt_dlp

log = logging.getLogger(__name__)

_ROOT = os.path.dirname(os.path.abspath(__file__))


def _cookies_file():
    """Resolve a cookies.txt for authenticated YouTube pulls (age/bot-gated videos).
    Same convention as tools/ytdlp_cookies.py; kept inline so the bot has no tools/ dependency.
    Order: YTDLP_COOKIES env, COOKIES env, then <repo>/secrets/cookies.txt. See COOKIES-SETUP.md."""
    for var in ("YTDLP_COOKIES", "COOKIES"):
        p = os.environ.get(var)
        if p:
            p = os.path.expanduser(os.path.expandvars(p.strip().strip('"')))
            if os.path.exists(p):
                return p
    default = os.path.join(_ROOT, "secrets", "cookies.txt")
    return default if os.path.exists(default) else None

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': False,
    'playlistend': 50,
    'nocheckcertificate': False,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': False,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


class Track:
    def __init__(self, data: dict):
        self.title = data.get('title') or 'Unknown'
        self.stream_url = data.get('url', '')
        if not self.stream_url:
            raise ValueError(f'Track "{self.title}" has no stream URL')
        self.webpage_url = data.get('webpage_url') or self.stream_url
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader') or ''

    def __repr__(self):
        return f'<Track title={self.title!r}>'


async def fetch_tracks(query: str) -> list[Track]:
    loop = asyncio.get_running_loop()

    def _extract():
        opts = dict(YTDL_OPTIONS)
        cookies = _cookies_file()
        if cookies:
            opts['cookiefile'] = cookies
        with yt_dlp.YoutubeDL(opts) as ytdl:
            try:
                data = ytdl.extract_info(query, download=False)
            except yt_dlp.utils.DownloadError as exc:
                raise ValueError(f'Download failed: {exc}') from exc
        return data

    data = await loop.run_in_executor(None, _extract)

    if not data:
        raise ValueError('No results found.')

    if 'entries' in data:
        entries = [e for e in data['entries'] if e and e.get('url')]
        skipped = sum(1 for e in data['entries'] if not e or not e.get('url'))
        if skipped:
            log.warning('Skipped %d unavailable entries in playlist', skipped)
        tracks = []
        for entry in entries:
            try:
                tracks.append(Track(entry))
            except ValueError:
                log.warning('Skipping entry with missing stream URL: %s', entry.get('title', '?'))
        if not tracks:
            raise ValueError('No playable tracks in playlist.')
        return tracks

    track = Track(data)
    if not track.stream_url:
        raise ValueError('No playable audio stream found.')
    return [track]
