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
from translation import translate_text

# ─── Configuration ──────────────────────────────────────────────────────────────

load_dotenv()

SAMPLE_RATE = 16000
CHUNK_SIZE = 4096
BYTES_PER_SAMPLE = 2
CHANNELS = 1

DEFAULT_SILENCE_THRESH_DBFS = -40
MIN_SILENCE_MS = 700
URGENT_FLUSH_SECONDS = 10
MIN_AUDIO_DURATION_SECONDS = 1.5
MIN_ACCUMULATED_DURATION = 2.0

INPUT_LANGUAGE = os.getenv("INPUT_LANGUAGE", "auto")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")  # New: output language setting

# ─── Globals ─────────────────────────────────────────────────────────────────────

audio_queue = queue.Queue()
playback_queue = queue.Queue()

SILENCE_THRESH_DBFS = DEFAULT_SILENCE_THRESH_DBFS
INPUT_DEVICE_INDEX = None
OUTPUT_DEVICE_NAME = None

# ─── Utility Functions ───────────────────────────────────────────────────────────

def has_enough_silence(audio_bytes, silence_thresh=SILENCE_THRESH_DBFS, silence_len=MIN_SILENCE_MS):
    audio = AudioSegment(
        data=audio_bytes,
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=CHANNELS
    )
    silent_chunks = silence.detect_silence(audio, min_silence_len=silence_len, silence_thresh=silence_thresh)
    return len(silent_chunks) > 0

def measure_ambient_noise(input_device_index, sample_time=2):
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
    return ambient_dbfs - 10

# ─── Audio Capture / Processing / Playback ───────────────────────────────────────

def capture_loop():
    audio_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=INPUT_DEVICE_INDEX)
    try:
        for chunk in audio_stream:
            timestamp = time.time()
            audio_queue.put((chunk, timestamp))
    except KeyboardInterrupt:
        print("\n🛑 Stopping audio capture.")

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

            if silence_detected or urgent_flush_needed:
                if buffer_duration_seconds >= MIN_AUDIO_DURATION_SECONDS:
                    print(f"[INFO] Flushing buffer ({buffer_duration_seconds:.2f}s)...")
                    flush_buffer(buffer, timestamps)
                    first_chunk_time = None
                elif buffer_duration_seconds >= MIN_ACCUMULATED_DURATION:
                    print(f"[INFO] Forcing flush of small accumulated buffer ({buffer_duration_seconds:.2f}s)...")
                    flush_buffer(buffer, timestamps)
                    first_chunk_time = None
                else:
                    print(f"[INFO] Holding small buffer ({buffer_duration_seconds:.2f}s), waiting...")

        except queue.Empty:
            print("[WARN] No new mic chunks.")

def flush_buffer(buffer, timestamps):
    chunk_to_process = bytes(buffer)
    timestamps_to_process = timestamps.copy()
    buffer.clear()
    timestamps.clear()
    threading.Thread(target=process_chunk, args=(chunk_to_process, timestamps_to_process)).start()

def process_chunk(chunk_to_process, timestamps):
    print("\n🛠️ Processing audio chunk...")
    if timestamps:
        lag_seconds = time.time() - timestamps[0]
        print(f"🕒 Current lag: {lag_seconds:.2f}s")

    try:
        use_translate = TARGET_LANGUAGE == "en" and INPUT_LANGUAGE != "en"

        raw_text = transcribe_audio(
            audio_chunk=chunk_to_process,
            sample_rate=SAMPLE_RATE,
            prompt="",
            language=INPUT_LANGUAGE,
            translate=use_translate
        )

        if raw_text:
            print(f"[Transcript] {raw_text}")

            if TARGET_LANGUAGE != "en":
                translated_text = translate_text(raw_text, target_language=TARGET_LANGUAGE)
                print(f"[Translated → {TARGET_LANGUAGE}] {translated_text}")
                tts_data = generate_audio(translated_text)
            else:
                tts_data = generate_audio(raw_text)

            if tts_data:
                playback_queue.put(tts_data)
            else:
                print("[WARN] No TTS data generated.")
        else:
            print("[WARN] No transcription text generated.")
    except Exception as e:
        print(f"[ERROR] Processing chunk failed: {e}")

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

# ─── Main Function ───────────────────────────────────────────────────────────────

def run_assistant(input_device_name, output_device_name=None):
    global SILENCE_THRESH_DBFS, INPUT_DEVICE_INDEX, OUTPUT_DEVICE_NAME

    print("🎙️ Starting real-time assistant…")

    INPUT_DEVICE_INDEX = find_input_device(input_device_name)
    if INPUT_DEVICE_INDEX is None:
        raise RuntimeError(f"Could not find input device containing '{input_device_name}'")

    OUTPUT_DEVICE_NAME = output_device_name

    print(f"[INFO] Using input device index {INPUT_DEVICE_INDEX} ({input_device_name})")

    SILENCE_THRESH_DBFS = measure_ambient_noise(INPUT_DEVICE_INDEX)
    print(f"[INFO] Using adaptive silence threshold: {SILENCE_THRESH_DBFS:.2f} dBFS")

    threading.Thread(target=capture_loop, daemon=True).start()
    threading.Thread(target=processing_loop, daemon=True).start()
    threading.Thread(target=playback_loop, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Assistant stopped manually.")

if __name__ == "__main__":
    run_assistant("MacBook Air Microphone")