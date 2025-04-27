# text_polish.py (new version using Groq and Gemma-2)

import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Retrieve API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in .env")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def polish_text(raw_text: str) -> str:
    """
    Send raw_text to Groq (Gemma-2 9b) and return polished text,
    preserving technical terms.
    """
    system_prompt = (
        "You are a real-time transcription polisher for a classroom assistant.\n"
        "Your task is to lightly edit the given text ONLY for grammar, clarity, and natural flow.\n"
        "You MUST preserve the speaker's original meaning, technical vocabulary, and intent exactly.\n"
        "Do NOT add new information, interpretations, or commentary.\n"
        "After polishing, internally double-check:\n"
        " - If the meaning has changed in any way, redo the polish to stay faithful.\n"
        " - If the meaning is preserved, output the polished text.\n"
        "Keep the tone conversational and informal if appropriate.\n"
        "Only correct grammar, minor phrasing, and awkward wording.\n"
    )


    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.3,
            max_tokens=300
        )

        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            return raw_text

    except Exception as e:
        print(f"[ERROR] Groq polishing failed: {e}")
        return raw_text