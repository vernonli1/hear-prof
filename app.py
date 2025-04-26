import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import time
import numpy as np
import requests
import os
import tempfile
import soundfile as sf
from dotenv import load_dotenv
load_dotenv()

# Set your Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this environment variable is set
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

# Choose the model
MODEL = "whisper-large-v3-turbo"  # Options: whisper-large-v3, distil-whisper-large-v3-en

# Initialize session state for transcription
if "transcription" not in st.session_state:
    st.session_state["transcription"] = ""

st.title("🎙️ Real-Time Transcription with Groq")
st.markdown("Speak into your microphone, and see the transcription below:")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = np.array([], dtype=np.float32)

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray().flatten().astype(np.float32) / 32768.0
        self.buffer = np.concatenate((self.buffer, audio))
        
        # Process every ~5 seconds of audio (assuming 48kHz sample rate)
        if len(self.buffer) >= 240000:
            # # Save audio to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                sf.write(tmpfile.name, self.buffer, 48000)
                tmpfile_path = tmpfile.name

            # Send audio to Groq API
            with open(tmpfile_path, "rb") as f:
                response = requests.post(
                    GROQ_URL,
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                    files={"file": f},
                    data={"model": MODEL}
                )
            if response.status_code == 200:
                result = response.json()
                print(result)
                transcript = result.get("text", "")

                st.session_state["transcription"] += f"\n{transcript}"
                
            else:
                st.error(f"Transcription failed: {response.text}")

            # Clear buffer
            self.buffer = np.array([], dtype=np.float32)

        return frame

webrtc_streamer(
    key="transcriber",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
)

st.subheader("📝 Transcription")
transcription_placeholder = st.empty()

while True:
    transcription_placeholder.markdown(st.session_state["transcription"])
    time.sleep(1)  # Update every 1 second