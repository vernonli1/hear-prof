import simpleaudio as sa

def play_audio(audio_data):
    if not audio_data:
        return
    
    play_obj = sa.play_buffer(audio_data, 1, 2, 22050)  # Mono, 2 bytes/sample, sample rate
    play_obj.wait_done()