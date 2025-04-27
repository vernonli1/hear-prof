import os
import wave
import tempfile
from dotenv import load_dotenv
from groq import Groq

# Load your Groq API key from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)

def transcribe_audio(audio_chunk: bytes,
                     sample_rate: int = 16000,
                     prompt: str = "") -> str | None:
    """
    1) Write raw PCM bytes into a real temp WAV file on disk
    2) Open that file and pass the file handle straight into Groq SDK
    3) Clean up and return the transcription text
    """
    tmp_path = None
    try:
        # 1) Create a real temp WAV file
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp_file.name
        tmp_file.close()

        # 2) Write raw mic bytes into that WAV
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)             # mono
            wf.setsampwidth(2)             # 16-bit PCM
            wf.setframerate(sample_rate)   # e.g. 16000 Hz
            wf.writeframes(audio_chunk)

        # 3) Open the temp file and send to Groq
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                file=audio_file,                   # real file handle
                model="whisper-large-v3-turbo",    # high-speed Whisper
                prompt=prompt,                     # optional context hint
                response_format="text",            # plain text response
                temperature=0.0                    # deterministic output
            )

        # 4) Handle SDK’s response type
        if isinstance(result, str):
            return result.strip()
        else:
            # if you switch to JSON output later, .text will exist
            return getattr(result, "text", str(result)).strip()

    except Exception as e:
        print(f"[ERROR] Groq Transcription failed: {e}")
        return None

    finally:
        # 5) Clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)