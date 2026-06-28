import asyncio
import yt_dlp

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
        self.webpage_url = data.get('webpage_url') or self.stream_url
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader') or ''

    def __repr__(self):
        return f'<Track title={self.title!r}>'


async def fetch_tracks(query: str) -> list[Track]:
    loop = asyncio.get_running_loop()

    def _extract():
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
            data = ytdl.extract_info(query, download=False)
        return data

    data = await loop.run_in_executor(None, _extract)

    if not data:
        raise ValueError('No results found.')

    if 'entries' in data:
        tracks = [Track(e) for e in data['entries'] if e and e.get('url')]
        if not tracks:
            raise ValueError('No playable tracks in playlist.')
        return tracks

    track = Track(data)
    if not track.stream_url:
        raise ValueError('No playable audio stream found.')
    return [track]
