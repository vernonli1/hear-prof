# main.py (threaded processing version)

import os
import time
import threading
import queue
from dotenv import load_dotenv
from threading import Semaphore

from audio_capture import capture_audio
from transcription import transcribe_audio
from text_polish import polish_text
from tts_generation import generate_audio
from audio_playback import play_audio
from utils.audio_devices import find_input_device

# ─── Configuration ──────────────────────────────────────────────────────────────

load_dotenv()

SAMPLE_RATE    = 16000
CHUNK_SIZE     = 4096
WINDOW_SECONDS = 3
BYTES_PER_SAMPLE = 2  # 16-bit PCM = 2 bytes
CHANNELS = 1

BYTES_PER_SECOND = SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNELS
WINDOW_BYTES = int(WINDOW_SECONDS * BYTES_PER_SECOND)

tts_semaphore = Semaphore(2)

# ─── Globals ─────────────────────────────────────────────────────────────────────

audio_queue = queue.Queue()

# ─── Functions ───────────────────────────────────────────────────────────────────

def capture_loop(input_device_index=None):
    """
    Continuously capture audio and push (chunk, timestamp) into the queue.
    """
    audio_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)

    try:
        for chunk in audio_stream:
            timestamp = time.time()
            audio_queue.put((chunk, timestamp))
    except KeyboardInterrupt:
        print("\n🛑 Stopping audio capture.")
    finally:
        print("[INFO] Capture thread exiting.")

def process_chunk(chunk_to_process, timestamps):
    """
    Process a chunk: transcribe, polish, generate TTS, and play it.
    Runs inside its own thread.
    """
    # LAG MONITOR
    oldest_ts = timestamps[0] if timestamps else time.time()
    lag_seconds = time.time() - oldest_ts
    print(f"🕒 Current lag behind live: {lag_seconds:.2f} seconds")

    print("\n🛠️  Processing audio chunk…")

    # 1) Transcribe
    raw_text = None
    try:
        raw_text = transcribe_audio(
            audio_chunk=chunk_to_process,
            sample_rate=SAMPLE_RATE,
            prompt=""
        )
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")

    if raw_text:
        print(f"[Raw Transcript] {raw_text}")
    
        polished = raw_text

        # # 2) Polish
        # polished = None
        # try:
        #     polished = polish_text(raw_text)
        # except Exception as e:
        #     print(f"[ERROR] Text polishing failed: {e}")
        #     polished = raw_text  # fallback

        # if polished:
        #     print(f"[Polished Transcript] {polished}")

        # 3) Generate TTS
        tts_data = None
        try:
            with tts_semaphore:
                tts_data = generate_audio(polished)
        except Exception as e:
            print(f"[ERROR] TTS generation failed: {e}")

        if tts_data:
            # 4) Play audio
            try:
                play_audio(tts_data)
            except Exception as e:
                print(f"[ERROR] Playback failed: {e}")
        else:
            print("[WARN] No TTS data generated.")

    else:
        print("[WARN] No transcription text generated.")

def processing_loop():
    """
    Accumulate chunks until WINDOW_BYTES collected, then spawn processing thread.
    """
    buffer = bytearray()
    timestamps = []

    while True:
        try:
            # Block until next (chunk, timestamp) arrives
            chunk, timestamp = audio_queue.get(timeout=5)
            buffer += chunk
            timestamps.append(timestamp)

            if len(buffer) >= WINDOW_BYTES:
                chunk_to_process = bytes(buffer[:WINDOW_BYTES])
                timestamps_to_process = timestamps[:len(buffer) // CHUNK_SIZE]
                
                buffer = buffer[WINDOW_BYTES:]  # remove processed part
                timestamps = timestamps[len(timestamps_to_process):]

                # Start a new processing thread!
                thread = threading.Thread(target=process_chunk, args=(chunk_to_process, timestamps_to_process))
                thread.start()

        except queue.Empty:
            print("[WARN] Audio queue timeout — no new chunks.")

# ─── Main Entry ─────────────────────────────────────────────────────────────────

def main():
    mic_name = "MacBook Air Microphone"
    MACBOOK_MIC_INDEX = find_input_device(mic_name)

    if MACBOOK_MIC_INDEX is None:
        raise RuntimeError(f"Could not find input device containing '{mic_name}'")

    print(f"[INFO] Using input device index {MACBOOK_MIC_INDEX} for microphone '{mic_name}'")
    print("🎙️ Starting real-time classroom assistant… speak into the mic (Ctrl-C to stop).")

    # Launch capture thread
    capture_thread = threading.Thread(target=capture_loop, args=(MACBOOK_MIC_INDEX,), daemon=True)
    capture_thread.start()

    # Run processing loop (main thread)
    try:
        processing_loop()
    except KeyboardInterrupt:
        print("\n🛑 Stopping assistant.")

if __name__ == "__main__":
    main()