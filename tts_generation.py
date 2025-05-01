# tts_generation.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
DEFAULT_VOICE_ID = os.getenv("TTS_VOICE_ID")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")

if not ELEVEN_API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY not set in .env")
if not DEFAULT_VOICE_ID:
    raise RuntimeError("TTS_VOICE_ID not set in .env")

def generate_audio(text: str, voice_id: str = None) -> bytes | None:
    """
    Send polished text to ElevenLabs and return the full audio container as bytes.
    Dynamically accepts voice_id for flexibility.
    Falls back to language-specific mapping if not provided.
    """
    # Use provided voice_id, or select based on language map
    if voice_id is None:
        voice_id = DEFAULT_VOICE_ID

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            return resp.content
        else:
            print(f"[ERROR] TTS failed {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"[ERROR] TTS exception: {e}")
        return None