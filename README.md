### What Our Project does

HearSay transcribes lectures (all kinds of speech really) in real-time and dictates it back to you in an understandable voice. It allows students to easily summarise their lecture transcriptions and generate study summaries, flashcards, and other study materials, which is organised on our platform. It also allows students to integrate visual study materials such as pictures of class whiteboards, PDFs, and Powerpoints which is integrated into their study notes.

### How we built HearSay

We built our web app on top of Streamlit. We used OpenAI's Whisper model for Speech-To-Text, Eleven Labs for Text-To-Speech as well as performing post-processing on audio recordings using PyAudio, PyDub and other Python packages. We used Llama for OCR on visual study materials and text summarisation. We stored audio transcripts and other study materials on MongoDB Atlas. Finally, we accelerated all our AI inference using Groq.

### Demo
[![Watch the demo](https://img.youtube.com/vi/PI1DPuL0iRk/hqdefault.jpg)](https://www.youtube.com/embed/PI1DPuL0iRk?si=wTvBs2bL51u9xGnd)

### Running the App

#### Downloads
Running the app locally will require the following downloads (for a Linux environment):

```
apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    libsndfile1-dev \
    build-essential \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

python -m pip install --upgrade pip
```

For a macOS environment, you will similarly need to download `pip` and `portaudio`.

After, for all plaforms, run:
```
pip install -r requirements.txt
```

#### Environment Variables

You will also need to create a `.env` folder in the `root` directory, and the following API keys:
```
GROQ_API_KEY={get free API key from https://groq.com/}
GEMINI_API_KEY={get free API key from https://aistudio.google.com/}
ELEVENLABS_API_KEY={get free API key from https://elevenlabs.io}
TTS_VOICE_ID={insert default voice ID from https://elevenlabs.io/docs/api-reference/voices/get}
MONGO_CONNECTION={insert MongoDB Atlas database connection string, from https://www.mongodb.com/products/platform/atlas-database}
```

Then, run:
```
streamlit run app.py
```

