import os
import time
import threading
import queue
from dotenv import load_dotenv
from pydub import AudioSegment, silence

from audio_capture import capture_audio
from transcription import transcribe_audio
from tts_generation import generate_audio
from audio_playback import play_audio
from utils.audio_devices import find_input_device

# ─── Configuration ──────────────────────────────────────────────────────────────

load_dotenv()

SAMPLE_RATE = 16000
CHUNK_SIZE = 4096
BYTES_PER_SAMPLE = 2
CHANNELS = 1

DEFAULT_SILENCE_THRESH_DBFS = -40  # fallback
MIN_SILENCE_MS = 700               # ms
URGENT_FLUSH_SECONDS = 10           # seconds
MIN_AUDIO_DURATION_SECONDS = 1.5    # seconds

# ─── Globals ─────────────────────────────────────────────────────────────────────

audio_queue = queue.Queue()
playback_queue = queue.Queue()

SILENCE_THRESH_DBFS = DEFAULT_SILENCE_THRESH_DBFS  # will update dynamically

# ─── Utility: Silence Detector ───────────────────────────────────────────────────

def has_enough_silence(audio_bytes, silence_thresh=SILENCE_THRESH_DBFS, silence_len=MIN_SILENCE_MS):
    audio = AudioSegment(
        data=audio_bytes,
        sample_width=2,  # 16-bit PCM
        frame_rate=SAMPLE_RATE,
        channels=CHANNELS
    )
    silent_chunks = silence.detect_silence(audio, min_silence_len=silence_len, silence_thresh=silence_thresh)
    return len(silent_chunks) > 0

def measure_ambient_noise(input_device_index, sample_time=2):
    """Capture a few seconds of audio and measure ambient dBFS level."""
    print("[INFO] Measuring ambient noise...")
    p = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)
    buffer = bytearray()

    start = time.time()
    while time.time() - start < sample_time:
        try:
            buffer.extend(next(p))
        except StopIteration:
            break

    if len(buffer) == 0:
        print("[WARN] No ambient audio captured.")
        return DEFAULT_SILENCE_THRESH_DBFS

    audio = AudioSegment(
        data=buffer,
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=1
    )

    ambient_dbfs = audio.dBFS
    print(f"[INFO] Measured ambient noise level: {ambient_dbfs:.2f} dBFS")

    return ambient_dbfs - 10  # 🔥 Target silence threshold 10dB lower than ambient

# ─── Capture Loop ────────────────────────────────────────────────────────────────

def capture_loop(input_device_index=None):
    audio_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)
    try:
        for chunk in audio_stream:
            timestamp = time.time()
            audio_queue.put((chunk, timestamp))
    except KeyboardInterrupt:
        print("\n🛑 Stopping audio capture.")

# ─── Processing Loop ─────────────────────────────────────────────────────────────

def processing_loop():
    buffer = bytearray()
    timestamps = []
    first_chunk_time = None

    while True:
        try:
            chunk, timestamp = audio_queue.get(timeout=5)
            buffer += chunk
            timestamps.append(timestamp)

            if first_chunk_time is None:
                first_chunk_time = timestamp

            current_time = time.time()

            buffer_duration_seconds = len(buffer) / (SAMPLE_RATE * CHANNELS * BYTES_PER_SAMPLE)

            silence_detected = has_enough_silence(buffer)
            urgent_flush_needed = (current_time - first_chunk_time) >= URGENT_FLUSH_SECONDS

            if (silence_detected or urgent_flush_needed) and buffer_duration_seconds >= MIN_AUDIO_DURATION_SECONDS:
                chunk_to_process = bytes(buffer)
                timestamps_to_process = timestamps.copy()

                buffer.clear()
                timestamps.clear()
                first_chunk_time = None

                threading.Thread(target=process_chunk, args=(chunk_to_process, timestamps_to_process)).start()

            elif (silence_detected or urgent_flush_needed) and buffer_duration_seconds < MIN_AUDIO_DURATION_SECONDS:
                print(f"[WARN] Discarded tiny buffer ({buffer_duration_seconds:.2f}s)")
                buffer.clear()
                timestamps.clear()
                first_chunk_time = None

        except queue.Empty:
            print("[WARN] No new mic chunks.")

# ─── Chunk Processing ────────────────────────────────────────────────────────────

def process_chunk(chunk_to_process, timestamps):
    print("\n🛠️  Processing audio chunk…")

    if timestamps:
        oldest_ts = timestamps[0]
        lag_seconds = time.time() - oldest_ts
        print(f"🕒 Current lag behind live: {lag_seconds:.2f} seconds")

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
        print(f"[Transcript] {raw_text}")

        tts_data = None
        try:
            tts_data = generate_audio(raw_text)
        except Exception as e:
            print(f"[ERROR] TTS generation failed: {e}")

        if tts_data:
            playback_queue.put(tts_data)
        else:
            print("[WARN] No TTS data generated.")
    else:
        print("[WARN] No transcription text generated.")

# ─── Playback Loop ───────────────────────────────────────────────────────────────

def playback_loop():
    while True:
        tts_data = playback_queue.get()
        try:
            if tts_data:
                play_audio(tts_data)
        except Exception as e:
            print(f"[ERROR] Playback failed: {e}")
        finally:
            playback_queue.task_done()

# ─── Main Entry ──────────────────────────────────────────────────────────────────

def main():
    global SILENCE_THRESH_DBFS

    print("🎙️ Starting real-time classroom assistant… speak into the mic (Ctrl-C to stop).")

    mic_name = "MacBook Air Microphone"
    MACBOOK_MIC_INDEX = find_input_device(mic_name)

    if MACBOOK_MIC_INDEX is None:
        raise RuntimeError(f"Could not find input device containing '{mic_name}'")

    print(f"[INFO] Using input device index {MACBOOK_MIC_INDEX} for microphone '{mic_name}'")

    # 🔥 Measure ambient noise and adapt silence threshold
    SILENCE_THRESH_DBFS = measure_ambient_noise(MACBOOK_MIC_INDEX)

    print(f"[INFO] Using adaptive silence threshold: {SILENCE_THRESH_DBFS:.2f} dBFS")

    # Start threads
    capture_thread = threading.Thread(target=capture_loop, args=(MACBOOK_MIC_INDEX,), daemon=True)
    capture_thread.start()

    processing_thread = threading.Thread(target=processing_loop, daemon=True)
    processing_thread.start()

    playback_thread = threading.Thread(target=playback_loop, daemon=True)
    playback_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping assistant.")

if __name__ == "__main__":
    main()