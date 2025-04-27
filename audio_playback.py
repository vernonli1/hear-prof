import io
import simpleaudio as sa
from pydub import AudioSegment

def play_audio(audio_data: bytes) -> None:
    """
    Decode ElevenLabs MP3 bytes via pydub, then play raw PCM frames with simpleaudio.
    """
    if not audio_data:
        return

    # 1) Load the MP3 into a pydub AudioSegment
    buf = io.BytesIO(audio_data)
    audio_seg = AudioSegment.from_file(buf, format="mp3")

    # 2) Extract raw PCM data and parameters
    raw_data   = audio_seg.raw_data
    nchannels  = audio_seg.channels
    sampwidth  = audio_seg.sample_width
    framerate  = audio_seg.frame_rate

    # 3) Play via simpleaudio
    play_obj = sa.play_buffer(raw_data, nchannels, sampwidth, framerate)
    play_obj.wait_done()