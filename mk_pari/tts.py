"""Text-to-speech for Pari's voice via ElevenLabs (supports Gujarati, Hindi, English).

Pick a female voice in the ElevenLabs voice library, name it "Pari", and put
its id in ELEVENLABS_VOICE_ID.
"""

from __future__ import annotations

import httpx2 as httpx


def speak(text: str, api_key: str | None, voice_id: str | None) -> bytes | None:
    """Return MP3 bytes, or None when TTS isn't configured."""
    if not (api_key and voice_id and text.strip()):
        return None
    r = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
        json={"text": text, "model_id": "eleven_multilingual_v2"},
        timeout=60,
    )
    r.raise_for_status()
    return r.content
