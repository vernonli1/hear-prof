# Final assistant_backend.py

import threading
import queue
import time
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore", message="missing ScriptRunContext!")
import pymongo
import pyaudio
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from tts_generation import generate_audio
from audio_capture import capture_audio
from audio_playback import play_audio
from list_audio_devices import list_devices
from pydub import AudioSegment, silence
import streamlit.runtime.scriptrunner as scriptrunner

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

# Initialize clients
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")
mongo_client = pymongo.MongoClient(MONGO_CONNECTION)
db = mongo_client["materials"]
collection = db["transcripts"]

MODEL = "whisper-large-v3-turbo"

# Globals
current_transcript_lines = []
audio_queue = queue.Queue()
playback_queue = queue.Queue()

# ElevenLabs Voice IDs Mapping
ELEVENLABS_VOICE_IDS = {
    "Voice 1": "21m00Tcm4TlvDq8ikWAM",    # Rachel
    "Voice 2": "CYw3kZ02Hs0563khs1Fj",    # Dave
    "Voice 3": "bVMeCyTHy58xNoL34h3p"     # Jeremy
}

# Configs
speaking_threshold = 0.01  # RMS threshold for speech detection
assistant_running_flag = threading.Event()

# --- Utilities ---
def detect_speaking(audio_np):
    rms = np.sqrt(np.mean(audio_np**2))
    return rms > speaking_threshold

def current_volume_level():
    # Fake value if not speaking
    return 20 if assistant_running_flag.is_set() else 0

# --- Transcription ---
def transcribe_audio_bytes(audio_bytes):
    import tempfile
    import wave
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        with wave.open(tmpfile.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes)
    with open(tmpfile.name, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model=MODEL,
            response_format="text",
            temperature=0.0,
        )
    return result.strip()

# --- Threads ---
def capture_loop(input_device_index=None):
    scriptrunner.add_script_run_ctx(threading.current_thread())
    mic_stream = capture_audio(chunk=CHUNK_SIZE, rate=SAMPLE_RATE, input_device_index=input_device_index)
    for chunk in mic_stream:
        if not assistant_running_flag.is_set():
            break
        audio_queue.put(chunk)

def processing_loop():
    scriptrunner.add_script_run_ctx(threading.current_thread())
    global current_transcript
    buffer = bytearray()
    last_flush = time.time()

    while assistant_running_flag.is_set():
        try:
            chunk = audio_queue.get(timeout=1)
            buffer.extend(chunk)

            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0

            duration_sec = len(buffer) / (SAMPLE_RATE * BYTES_PER_SAMPLE)

            if duration_sec >= 2 or (time.time() - last_flush) > 5:
                transcript = transcribe_audio_bytes(buffer)
                if transcript:
                    current_transcript_lines.append(transcript.strip())
                    try:
                        # Fetch the current selected voice
                        chosen_voice = st.session_state.get("chosen_voice", "Voice 1")
                        voice_id = ELEVENLABS_VOICE_IDS.get(chosen_voice, ELEVENLABS_VOICE_IDS["Voice 1"])

                        # Pass the voice_id into generate_audio
                        tts_audio = generate_audio(transcript, voice_id=voice_id)

                        if tts_audio:
                            playback_queue.put(tts_audio)
                    except Exception as e:
                        print(f"[ERROR] TTS failed: {e}")

                buffer = bytearray()
                last_flush = time.time()

        except queue.Empty:
            pass

def playback_loop():
    scriptrunner.add_script_run_ctx(threading.current_thread())
    while assistant_running_flag.is_set():
        try:
            audio_data = playback_queue.get(timeout=1)
            play_audio(audio_data)
        except queue.Empty:
            pass

# --- Main API ---
def start_assistant(input_device_name, output_device_name):
    assistant_running_flag.set()

    # Find input device index manually
    p = pyaudio.PyAudio()
    input_device_index = None
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev.get('maxInputChannels') > 0 and input_device_name.lower() in dev.get('name').lower():
            input_device_index = i
            break
    p.terminate()

    if input_device_index is None:
        raise RuntimeError(f"Could not find input device containing '{input_device_name}'")

    print(f"[INFO] Using input device index {input_device_index} ({input_device_name})")

    threading.Thread(target=capture_loop, args=(input_device_index,), daemon=True).start()
    threading.Thread(target=processing_loop, daemon=True).start()
    threading.Thread(target=playback_loop, daemon=True).start()

def stop_assistant():
    assistant_running_flag.clear()

def save_transcript_to_mongo(transcript_text, chosen_voice="Unknown", lecture_name="Unnamed"):
    try:
        doc = {
            "name": lecture_name,
            "transcript": transcript_text.strip(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "voice": chosen_voice
        }
        collection.insert_one(doc)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save transcript to MongoDB: {e}")
        return False

def list_audio_devices():
    """List input and output devices separately."""
    p = pyaudio.PyAudio()
    input_devices = []
    output_devices = []

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev.get("maxInputChannels") > 0:
            input_devices.append(dev.get("name"))
        if dev.get("maxOutputChannels") > 0:
            output_devices.append(dev.get("name"))

    p.terminate()
    return input_devices, output_devices
