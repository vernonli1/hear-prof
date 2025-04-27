### What Our Project does

HearSay transcribes lectures (all kinds of speech really) in real-time and dictates it back to you in an understandable voice. It allows students to easily summarise their lecture transcriptions and generate study summaries, flashcards, and other study materials, which is organised on our platform. It also allows students to integrate visual study materials such as pictures of class whiteboards, PDFs, and Powerpoints which is integrated into their study notes.

### How we built HearSay

We built our web app on top of Streamlit. We used OpenAI's Whisper model for Speech-To-Text, Eleven Labs for Text-To-Speech as well as performing post-processing on audio recordings using PyAudio, PyDub and other Python packages. We used Llama for OCR on visual study materials and text summarisation. We stored audio transcripts and other study materials on MongoDB Atlas. Finally, we accelerated all our AI inference using Groq.
