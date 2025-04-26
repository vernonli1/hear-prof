# main.py

import os
import time
from dotenv import load_dotenv

from audio_capture import capture_audio
from transcription import transcribe_audio
from text_polish import polish_text
from tts_generation import generate_audio
from audio_playback import play_audio

# ─── Configuration ─────────────────────────────────────────────────────────────

load_dotenv()  # loads GROQ_API_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY, TTS_VOICE_ID

SAMPLE_RATE    = 16000     # must match your audio_capture rate
CHUNK_SIZE     = 4096      # frames per buffer read
WINDOW_SECONDS = 3         # seconds of audio per transcription window

# ─── Main Loop ─────────────────────────────────────────────────────────────────

def main():
    print("🎙️ Starting real-time classroom assistant… speak into the mic (Ctrl-C to stop).")

    audio_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE)
    buffer_bytes = b""
    window_start = time.time()

    try:
        for chunk in audio_stream:
            buffer_bytes += chunk

            # once we've collected ~WINDOW_SECONDS of audio
            if time.time() - window_start >= WINDOW_SECONDS:
                print("\n🛠️  Processing audio chunk…")

                # 1) Transcribe via Groq Whisper
                raw_text = transcribe_audio(
                    audio_chunk=buffer_bytes,
                    sample_rate=SAMPLE_RATE,
                    prompt=""  # you can set context here
                )

                if raw_text:
                    print(f"[Raw Transcript] {raw_text}")

                    # 2) Polish with Gemini
                    polished = polish_text(raw_text)
                    print(f"[Polished Transcript] {polished}")

                    # 3) Generate TTS audio
                    tts_data = generate_audio(polished)
                    if tts_data:
                        # 4) Play it back
                        play_audio(tts_data)
                    else:
                        print("[WARN] TTS generation returned nothing")

                else:
                    print("[WARN] Transcription returned nothing")

                # reset for next window
                buffer_bytes = b""
                window_start = time.time()

    except KeyboardInterrupt:
        print("\n🛑 Stopping assistant.")

if __name__ == "__main__":
    main()