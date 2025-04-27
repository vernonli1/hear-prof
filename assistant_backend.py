# assistant_backend.py

import threading
import time
import queue
import os
from dotenv import load_dotenv
from pydub import AudioSegment, silence

from audio_capture import capture_audio
from transcription import transcribe_audio
from tts_generation import generate_audio
from audio_playback import play_audio
from utils.audio_devices import find_input_device

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

# Shared Queues
audio_queue = queue.Queue()
playback_queue = queue.Queue()

SILENCE_THRESH_DBFS = DEFAULT_SILENCE_THRESH_DBFS

# Shared transcript storage
current_transcript = ""

# ─── Utility Functions ────────────────────────────────────────────────────────

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
    p = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)
    buffer = bytearray()

    start = time.time()
    while time.time() - start < sample_time:
        try:
            buffer.extend(next(p))
        except StopIteration:
            break

    if len(buffer) == 0:
        return DEFAULT_SILENCE_THRESH_DBFS

    audio = AudioSegment(
        data=buffer,
        sample_width=2,
        frame_rate=SAMPLE_RATE,
        channels=1
    )

    ambient_dbfs = audio.dBFS
    return ambient_dbfs - 10

# ─── Main Loops ───────────────────────────────────────────────────────────────

def capture_loop(input_device_index=None):
    audio_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)
    for chunk in audio_stream:
        timestamp = time.time()
        audio_queue.put((chunk, timestamp))

def processing_loop():
    global current_transcript
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
                    flush_buffer(buffer, timestamps)
                    first_chunk_time = None
                elif buffer_duration_seconds >= MIN_ACCUMULATED_DURATION:
                    flush_buffer(buffer, timestamps)
                    first_chunk_time = None

        except queue.Empty:
            continue

def flush_buffer(buffer, timestamps):
    chunk_to_process = bytes(buffer)
    timestamps_to_process = timestamps.copy()

    buffer.clear()
    timestamps.clear()

    threading.Thread(target=process_chunk, args=(chunk_to_process, timestamps_to_process)).start()

def process_chunk(chunk_to_process, timestamps):
    global current_transcript

    raw_text = transcribe_audio(audio_chunk=chunk_to_process, sample_rate=SAMPLE_RATE)

    if raw_text:
        current_transcript += raw_text.strip() + "\n"

        tts_data = generate_audio(raw_text)
        if tts_data:
            playback_queue.put(tts_data)

def playback_loop():
    while True:
        tts_data = playback_queue.get()
        try:
            if tts_data:
                play_audio(tts_data)
        finally:
            playback_queue.task_done()

# ─── Main Starter ─────────────────────────────────────────────────────────────

def start_assistant():
    global SILENCE_THRESH_DBFS

    mic_name = "MacBook Air Microphone"
    MACBOOK_MIC_INDEX = find_input_device(mic_name)

    if MACBOOK_MIC_INDEX is None:
        raise RuntimeError(f"Could not find input device containing '{mic_name}'")

    SILENCE_THRESH_DBFS = measure_ambient_noise(MACBOOK_MIC_INDEX)

    threading.Thread(target=capture_loop, args=(MACBOOK_MIC_INDEX,), daemon=True).start()
    threading.Thread(target=processing_loop, daemon=True).start()
    threading.Thread(target=playback_loop, daemon=True).start()

    print("[Assistant] All threads started.")