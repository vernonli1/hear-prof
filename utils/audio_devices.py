import pyaudio

def find_input_device(name_contains: str) -> int | None:
    """
    Find input device index where device name contains the given string (case insensitive).
    Returns None if no matching device is found.
    """
    p = pyaudio.PyAudio()
    num_devices = p.get_device_count()

    for i in range(num_devices):
        device_info = p.get_device_info_by_index(i)
        device_name = device_info.get('name', '').lower()
        max_input_channels = device_info.get('maxInputChannels', 0)

        if name_contains.lower() in device_name and max_input_channels > 0:
            return i

    return None