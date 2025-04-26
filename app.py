import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import os
import soundfile as sf
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Set up Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this environment variable is set
MODEL = "whisper-large-v3-turbo"  # Options: whisper-large-v3, distil-whisper-large-v3-en
client = Groq(api_key=GROQ_API_KEY)

if "transcription" not in st.session_state:
    st.session_state["transcription"] = ""

st.title("🎙️ Real-Time Transcription with Groq")
st.markdown("Speak into your microphone, and see the transcription below:")


# Streamlit code
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.buffer = np.array([], dtype=np.float32)

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        
        audio = frame.to_ndarray().flatten().astype(np.float32) / 32768.0
        self.buffer = np.concatenate((self.buffer, audio))

        # Process every ~5 seconds of audio
        if len(self.buffer) >= 240000:  # 5 sec at 48kHz
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                sf.write(tmpfile.name, self.buffer, 48000)
                tmpfile_path = tmpfile.name

            try:
                # Call the transcribe_audio function to process and transcribe
                transcript = transcribe_audio(tmpfile_path)

                print(transcript)

                st.session_state['transcription'] += transcript
                

                # Force Streamlit to rerun and update the markdown
                st.rerun()

            except Exception as e:
                st.error(f"Transcription error: {e}")
                st.rerun()

            # Clear buffer after processing
            self.buffer = np.array([], dtype=np.float32)

        return frame

# Function to transcribe the audio
def transcribe_audio(file_path: str, prompt: str = "") -> str:
    """
    1) Write raw PCM bytes into a real temp WAV file on disk
    2) Open that file and pass the file handle straight into Groq SDK
    3) Clean up and return the transcription text
    """
    try:
        with open(file_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=audio_file,
                model=MODEL,
                prompt=prompt,
                response_format="text",  # plain text response
                temperature=0.0  # deterministic output
            )

        if isinstance(result, str):
            return result.strip()
        else:
            return getattr(result, "text", str(result)).strip()

    except Exception as e:
        print(f"[ERROR] Groq Transcription failed: {e}")
        return "Error in transcription."

# Start WebRTC streamer
webrtc_streamer(
    key="transcriber",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=False,  # <-- Important! Process everything synchronously
)


# Display the transcription with a markdown block that updates
st.subheader("📝 Transcription")
st.markdown(st.session_state["transcription"])
