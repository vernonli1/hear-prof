import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

def polish_text(raw_text):
    prompt = f"""Polish this academic lecture text for natural English clarity, but preserve all technical or mathematical vocabulary. Return plain text only.

Text:
{raw_text}
"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini polishing failed: {e}")
        return raw_text  # Fallback to raw if error