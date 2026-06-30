# Creators registry

The source list Zoey pulls from for future learning loops. The inventory found this missing --
video URLs were one-off in `tools/video-urls.txt` with no notion of WHO made them or how to get
new ones. This file is that registry. Format: name | platform | handle | role | notes.

## How it feeds the loop

- New content to learn from = new reels from these creators. The local watch (`watch-batch.sh`)
  reads URLs; this registry is the human-readable source-of-truth for which accounts those come
  from, so future pulls are "grab the latest from these handles" instead of hunting links.
- **Auto-fill the AI creators:** when Chris runs the watch locally, yt-dlp returns each video's
  uploader. The watch step can append the uploader handle here, so the list of AI/JARVIS/automation
  creators behind the 69 reels populates itself after the first run (the cloud can't see the
  handles -- Instagram is walled here). Until then their rows are placeholders to fill in.

## Chris's own brands (the content targets)

| Name | Platform | Handle | Role | Notes |
|---|---|---|---|---|
| Zenthra | TikTok / YouTube | (fill in) | own brand | Roblox guild content, "Zenith of Power" |
| Zenthra | Instagram | (fill in) | own brand | reels/posts source for video-urls.txt |
| Clearcoat Co. | TikTok | (fill in) | own brand | mobile detailing, business-verified |
| Clearcoat Co. | Instagram | (fill in) | own brand | before/after, booking pushes |

## AI / JARVIS / automation creators (the learning sources)

These are the accounts behind the 69 reels in `tools/video-urls.txt` (the 2026-06-30 batch).
Handles fill in from the local watch's uploader metadata after the first run.

| Name | Platform | Handle | Role | Notes |
|---|---|---|---|---|
| (auto-fill from watch) | Instagram | (uploader) | learning source | AI agent / JARVIS / automation builds |

## Use

- Add a creator here when you find one worth learning from.
- To pull their newest: paste their reel links into `tools/video-urls.txt`, run the local watch,
  then `digest-transcripts`. The registry keeps the "who" so the loop knows where to look next.
