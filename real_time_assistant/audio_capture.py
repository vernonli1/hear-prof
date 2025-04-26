import pyaudio

def capture_audio(chunk=4096, rate=16000):
    p = pyaudio.PyAudio()
    
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    print("[INFO] Microphone stream started...")
    
    try:
        while True:
            data = stream.read(chunk)
            yield data
    except KeyboardInterrupt:
        print("[INFO] Stopping audio capture.")
        stream.stop_stream()
        stream.close()
        p.terminate()