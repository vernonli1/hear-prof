import streamlit as st
import threading
import time
import re
from assistant_backend import (
    start_assistant,
    stop_assistant,
    current_transcript_lines,
    save_transcript_to_mongo,
    list_audio_devices
)


# Inject custom CSS
st.markdown("""
    <style>
    body { background-color: #0e1117; color: white; scroll-behavior: smooth; }
    .stButton>button {
        border-radius: 8px;
        padding: 0.75em 2em;
        font-weight: bold;
        background-color: #636efa;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #404EED;
        color: white;
    }
    .stTextArea>div>textarea {
        background-color: #1e222d;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
    <h1 style="text-align: center; color: #636efa;">🎙️ Real-Time Classroom Assistant</h1>
    <p style="text-align: center; font-size: 20px; color: #d1d1d1;">
        Instantly transcribe, translate, and voice-back your lectures in real-time.<br>
        Focus on learning. Let AI handle the listening.
    </p>
""", unsafe_allow_html=True)

st.divider()

# Sidebar Settings
st.sidebar.header("🎛️ Settings")

input_devices, output_devices = list_audio_devices()

input_device = st.sidebar.selectbox("Select Input Device 🎤", input_devices, index=0)
output_device = st.sidebar.selectbox("Select Output Device 🔊", output_devices, index=0)

voice_option = st.sidebar.selectbox(
    "Choose Voice",
    ("Voice 1", "Voice 2", "Voice 3")
)

# Save to session
st.session_state["chosen_voice"] = voice_option
st.session_state["input_device"] = input_device
st.session_state["output_device"] = output_device

# Assistant Status Indicator
if "assistant_running" not in st.session_state:
    st.session_state["assistant_running"] = False

col1, col2, col3 = st.columns(3)

if not st.session_state["assistant_running"]:
    if st.button("🚀 Launch Assistant"):
        threading.Thread(
            target=start_assistant,
            args=(input_device, output_device),
            daemon=True
        ).start()
        st.session_state["assistant_running"] = True
        st.rerun()
else:
    if st.button("🛑 Terminate Assistant"):
        stop_assistant()
        st.session_state["assistant_running"] = False
        st.rerun()

if st.session_state["assistant_running"]:
    st.success("🟢 Assistant is Running...")
else:
    st.warning("🔴 Assistant is Stopped.")

st.divider()

# Live Transcription Display
st.subheader("📄 Live Transcription (Focus View)")
transcript_display = st.empty()

# Settings
N_BRIGHT = 2  # number of latest sentences bright

if st.session_state["assistant_running"]:
    st.success("🟢 Transcript is live.")
    while st.session_state["assistant_running"]:
        full_text = " ".join(current_transcript_lines)

        # Split text into sentences
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(full_text)

        html_output = ""

        if len(sentences) <= N_BRIGHT:
            for s in sentences:
                html_output += f'<span style="opacity: 1.0;">{s} </span>'
        else:
            for s in sentences[:-N_BRIGHT]:
                html_output += f'<span style="opacity: 0.3;">{s} </span>'
            for s in sentences[-N_BRIGHT:-1]:
                html_output += f'<span style="opacity: 1.0;">{s} </span>'
            if sentences:
                html_output += f'<span style="background-color: #ffeb3b; color: black; font-weight: bold;">{sentences[-1]} </span>'

        transcript_display.markdown(html_output, unsafe_allow_html=True)
        time.sleep(1)

else:
    transcript_display.warning("🔴 Transcript is not live.")

st.divider()

# Smart Lecture Name Generation
def generate_title_from_transcript(transcript_text):
    try:
        excerpt = transcript_text[:300]
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": f"Generate a short 3-6 word academic lecture title from this excerpt:\n\n{excerpt}"}
            ]
        )
        title = response.choices[0].message.content.strip()
        return title
    except Exception as e:
        print(f"[ERROR] Failed to generate title: {e}")
        return "Untitled Lecture"

# Save Transcript Section
st.subheader("💾 Save Transcript")

# Auto-fill suggestion based on first few words
if current_transcript_lines:
    first_sentence = current_transcript_lines[0]
    suggested_name = " ".join(first_sentence.split()[:5]) + "..." if len(first_sentence.split()) > 5 else first_sentence
else:
    suggested_name = ""

lecture_name = st.text_input("Enter Lecture Name 📝", value=suggested_name, placeholder="e.g., Introduction to Biology")


if st.button("💾 Save Transcript"):
    if current_transcript_lines:
        full_transcript_text = "\n".join(current_transcript_lines)

        # Auto-generate a title suggestion
        suggested_title = generate_title_from_transcript(full_transcript_text)

        # Allow user to edit or accept the suggested title
        lecture_name = st.text_input("📝 Lecture Name", value=suggested_title)

        if st.button("✅ Confirm and Save"):
            save_success = save_transcript_to_mongo(full_transcript_text, lecture_name)
            if save_success:
                st.success("✅ Transcript saved to MongoDB!")
            else:
                st.error("❌ Failed to save transcript.")
    else:
        st.warning("⚠️ No transcript available to save.")


# Footer
st.markdown("""
    <hr style="margin-top: 3em;">
    <p style="text-align: center; font-size: 14px; color: #888;">
        Built with ❤️ by Team HearSay | LA Hacks 2025
    </p>
""", unsafe_allow_html=True)