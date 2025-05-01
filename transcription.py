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
                     prompt: str = "",
                     language: str = "auto",
                     translate: bool = False) -> str | None:
    """
    Transcribes or translates audio using Groq's Whisper API.
    Parameters:
        audio_chunk (bytes): Raw PCM audio data.
        sample_rate (int): Sampling rate of the audio.
        prompt (str): Optional prompt to guide transcription.
        language (str): Language code (e.g., 'en', 'es', 'fr'). Use 'auto' for auto-detection.
        translate (bool): If True, translates audio to English using supported model.
    Returns:
        str | None: Transcribed or translated text.
    """
    tmp_path = None
    try:
        # Create a temporary WAV file
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp_file.name
        tmp_file.close()

        # Write audio data to the WAV file
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)             # mono
            wf.setsampwidth(2)             # 16-bit PCM
            wf.setframerate(sample_rate)   # e.g., 16000 Hz
            wf.writeframes(audio_chunk)

        # Select model based on translate flag
        model_name = "whisper-large-v3" if translate else "whisper-large-v3-turbo"

        # Open the temp file and send to Groq
        with open(tmp_path, "rb") as audio_file:
            if translate:
                result = client.audio.translations.create(
                    file=audio_file,
                    model=model_name,
                    prompt=prompt,
                    response_format="text",
                    temperature=0.0
                )
            else:
                result = client.audio.transcriptions.create(
                    file=audio_file,
                    model=model_name,
                    prompt=prompt,
                    response_format="text",
                    temperature=0.0,
                    language=None if language == "auto" else language
                )

        # Handle the response
        if isinstance(result, str):
            return result.strip()
        else:
            return getattr(result, "text", str(result)).strip()

    except Exception as e:
        print(f"[ERROR] Groq Transcription failed: {e}")
        return None

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)