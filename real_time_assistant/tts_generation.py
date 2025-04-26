import requests

ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY"

def generate_audio(text, voice="Rachel"):
    url = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    body = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body, stream=True)
        if response.status_code == 200:
            return response.raw.read()
        else:
            print(f"[ERROR] TTS failed with status code {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERROR] TTS generation error: {e}")
        return None