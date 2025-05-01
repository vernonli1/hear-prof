# translation.py

from deep_translator import GoogleTranslator

def translate_text(text: str, target_language: str = "es") -> str:
    try:
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return text