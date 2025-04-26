import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import os
import time
import soundfile as sf
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


st.markdown("# Transcribe 🎈")
st.sidebar.header("Transcribe 🎈")

# Set up Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Ensure this environment variable is set
MODEL = "whisper-large-v3-turbo"  # Options: whisper-large-v3, distil-whisper-large-v3-en
client = Groq(api_key=GROQ_API_KEY)

if "transcription_sessions" not in st.session_state:
    st.session_state["transcription_sessions"] = []

if "current_session_transcription" not in st.session_state:
    st.session_state["current_session_transcription"] = ""

st.title("🎙️ Real-Time Transcription with Groq")
st.markdown("Speak into your microphone, and see the transcription below:")


# Streamlit code
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.current_transcription = ""
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

                self.current_transcription += transcript


                # Force Streamlit to rerun and update the markdown

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
webrtc_ctx = webrtc_streamer(
    key="transcriber",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=False,  # <-- Important! Process everything synchronously
)

transcription_display = st.empty()

if webrtc_ctx and webrtc_ctx.state.playing:
    # Setup a loop to update transcription while streaming
    while True:
        if webrtc_ctx.audio_processor:
            new_transcription = webrtc_ctx.audio_processor.current_transcription
            if new_transcription != st.session_state["current_session_transcription"]:
                st.session_state["current_session_transcription"] = new_transcription

                transcription_display.markdown(st.session_state["current_session_transcription"])
                

        time.sleep(1)  # <-- Poll every 1 second (adjust if you want faster updates)
elif not webrtc_ctx.state.playing:
    # When recording stops, push completed session to list
    if st.session_state["current_session_transcription"]:
        st.session_state["transcription_sessions"].append(
            st.session_state["current_session_transcription"]
        )
        st.session_state["current_session_transcription"] = ""


# Display the transcription with a markdown block that updates
st.subheader("📝 Transcription")
st.markdown("<br>".join(st.session_state["transcription_sessions"]), unsafe_allow_html=True)
