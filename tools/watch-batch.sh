#!/bin/bash
# Batch download videos and transcribe them with Groq Whisper.
#
# RUN THIS ON YOUR OWN COMPUTER, not the cloud session. The cloud proxy blocks
# Instagram (403), and your machine has your login. This is the fix for that wall.
#
# Needs: yt-dlp, ffmpeg, and a free GROQ_API_KEY (get one at https://groq.com).
# Reads URLs from a file, one per line. Writes one transcript .txt per video.
#
# Usage:
#   export GROQ_API_KEY=gsk_...
#   tools/watch-batch.sh tools/video-urls.txt transcripts/
#
# Then: git add transcripts/ && commit && push. Claude reads them and applies the lessons.
set -euo pipefail

URLS_FILE="${1:-tools/video-urls.txt}"
OUT="${2:-transcripts}"

[ -f "$URLS_FILE" ] || { echo "no url file: $URLS_FILE (put one URL per line)"; exit 1; }
: "${GROQ_API_KEY:?set GROQ_API_KEY (free at https://groq.com)}"
command -v yt-dlp >/dev/null || { echo "install yt-dlp first"; exit 1; }
command -v ffmpeg >/dev/null || { echo "install ffmpeg first"; exit 1; }
mkdir -p "$OUT"

i=0; ok=0; fail=0
while IFS= read -r url || [ -n "$url" ]; do
  url="$(echo "$url" | tr -d '[:space:]')"
  case "$url" in ""|\#*) continue ;; esac
  i=$((i+1))
  id="$(printf '%s' "$url" | grep -oE '/(reel|p|tv)/[^/?]+' | head -1 | sed 's@.*/@@')"
  [ -n "$id" ] || id="video_$i"
  base="$OUT/$id"
  if [ -s "$base.txt" ] && ! grep -q '^__FAILED__' "$base.txt"; then
    echo "[$i] $id already transcribed, skip"; ok=$((ok+1)); continue
  fi
  echo "[$i] $id downloading audio..."
  if ! yt-dlp -q --no-warnings -f 'bestaudio/best' -x --audio-format mp3 \
        -o "$base.%(ext)s" "$url" 2>/dev/null; then
    echo "[$i] $id download FAILED (login/blocked/removed)"; echo "__FAILED__ download" > "$base.txt"; fail=$((fail+1)); continue
  fi
  audio="$(ls "$base".mp3 2>/dev/null | head -1)"
  [ -n "$audio" ] || { echo "__FAILED__ no audio" > "$base.txt"; fail=$((fail+1)); continue; }
  echo "[$i] $id transcribing (Groq Whisper)..."
  if curl -sf https://api.groq.com/openai/v1/audio/transcriptions \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -F "model=whisper-large-v3" -F "response_format=text" \
        -F "file=@$audio" -o "$base.txt"; then
    ok=$((ok+1)); echo "[$i] $id done"
  else
    echo "__FAILED__ transcribe" > "$base.txt"; fail=$((fail+1)); echo "[$i] $id transcribe FAILED"
  fi
  rm -f "$audio"
  sleep 3   # polite to Instagram + Groq rate limits
done < "$URLS_FILE"

echo ""
echo "Done. $ok ok, $fail failed, out of $i. Transcripts in $OUT/"
echo "Next: git add $OUT && commit && push, then Claude reads them."
