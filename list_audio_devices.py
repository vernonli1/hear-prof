# list_audio_devices.py

import pyaudio

def list_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    print("Available Audio Devices:\n")

    for i in range(0, num_devices):
        device = p.get_device_info_by_host_api_device_index(0, i)
        print(f"Device {i}: {device.get('name')} (Input Channels: {device.get('maxInputChannels')}, Output Channels: {device.get('maxOutputChannels')})")

    p.terminate()

if __name__ == "__main__":
    list_devices()