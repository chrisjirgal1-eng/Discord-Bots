# JARVIS voice options (feminine, ElevenLabs)

Shortlist for a warm, feminine, JARVIS-style voice that talks back. All are ElevenLabs voices.
Preview them by name in the ElevenLabs voice library (elevenlabs.io > Voices), pick one, then the
chosen Voice ID goes in `.env` as `ELEVENLABS_VOICE_ID` and JARVIS speaks in it.

IDs below are the long-standing default Voice IDs, given as a convenience. Confirm the exact ID in
your own ElevenLabs account before wiring, since the library can change. Names are stable.

## Warm and intimate ("Her" / Samantha energy)

- Matilda. Warm, friendly, natural. The easiest to live with day to day. ID XrExE9yKIg1WjnnlVkGX
- Sarah. Soft, gentle, young American. Cozy and close. ID EXAVITQu4vr4xnSDxMaL

## Sultry (overtly alluring)

- Charlotte. Sultry and seductive with a slight European lilt. The "sexy" pick. ID XB0fDUnXU5powFXDhCwa
- Nicole. Breathy, near-whisper, very intimate. ASMR-soft. ID piTKgcLEGmPE4e6mEKli

## Elegant British (JARVIS, female and classy)

- Lily. Warm British, refined and smooth. The classy "Her" vibe. ID pFZP5JQG7iQjIQuC4Bku
- Alice. Confident British, poised and commanding. ID Xb7hH8MSUJpSbSDYk0k2

## Confident and professional

- Rachel. Calm, clear, smooth. The reliable classic assistant. ID 21m00Tcm4TlvDq8ikWAM
- Jessica. Young, expressive, a touch playful and flirty. ID cgSgspJ2msm6clMCkdW9

## My picks

- Sexiest: Charlotte (sultry) or Nicole (breathy and intimate).
- Best all-rounder for a feminine JARVIS: Lily (elegant British, warm) or Matilda (warm American).
- If unsure, start with Charlotte for sexy or Lily for classy, both read great as an assistant.

Beyond these, the ElevenLabs Voice Library has thousands of community voices. Search "seductive",
"AI assistant", "Her", or "girlfriend" for more, or clone a custom voice.

## Wiring (one step once Chris picks and has a key)

1. `.env` (gitignored): `ELEVENLABS_API_KEY=...` and `ELEVENLABS_VOICE_ID=<the chosen ID>`.
2. Build the loop from `memory-bank/jarvis-voice-spec.md` (mic to Deepgram to claude -p jarvis to
   ElevenLabs to speaker). The chosen voice is what JARVIS speaks in.
