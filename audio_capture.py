import pyaudio

def capture_audio(chunk=4096, rate=16000, input_device_index=None):
    """
    Yields raw audio frames of size `chunk`. On buffer overflow, yields silence instead of crashing.
    """
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=rate,
        input=True,
        input_device_index=input_device_index,
        frames_per_buffer=chunk
    )

    print("[INFO] Microphone stream started…")

    try:
        while True:
            try:
                # Prevent OSError on overflow
                data = stream.read(chunk, exception_on_overflow=False)
            except OSError as e:
                print(f"[WARN] Input overflowed: {e}. Yielding silence for this chunk.")
                # 2 bytes per sample × chunk samples = chunk*2 bytes of silence
                data = b"\x00" * (chunk * 2)
            yield data

    finally:
        print("[INFO] Stopping audio capture.")
        stream.stop_stream()
        stream.close()
        p.terminate()