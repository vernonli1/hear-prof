import streamlit as st
st.set_page_config(page_title="Live Assistant 🎙️")
import threading
import time
import re
from assistant_backend import (
    start_assistant,
    stop_assistant,
    current_transcript_lines,
    save_transcript_to_mongo,
    list_audio_devices,
    summarize_image,
    image_summaries,
    uploaded_images
)
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama-3.3-70b-versatile"

# Hero Section
st.markdown("""
<h1 style="text-align: center; color: #636efa;">🎙️ Real-Time Classroom Assistant</h1>
<p style="text-align: center; font-size: 20px; color: #d1d1d1;">
    Transcribe, translate, and voice-back your lectures instantly.<br>
    Focus on learning. Let AI handle the listening.
</p>
""", unsafe_allow_html=True)

st.divider()

# Sidebar
st.sidebar.header("🎛️ Settings")
input_devices, output_devices = list_audio_devices()

input_device = st.sidebar.selectbox("Input Device 🎤", input_devices, index=0)
output_device = st.sidebar.selectbox("Output Device 🔊", output_devices, index=0)

voice_option = st.sidebar.selectbox(
    "Choose Voice",
    ("Voice 1", "Voice 2", "Voice 3")
)

st.session_state["chosen_voice"] = voice_option
st.session_state["input_device"] = input_device
st.session_state["output_device"] = output_device

# Assistant Controls
st.header("🚀 Launch / Terminate Assistant")

start_col, stop_col = st.columns(2)
start_button = start_col.button("🚀 Start Assistant")
stop_button = stop_col.button("🛑 Stop Assistant")

if "assistant_running" not in st.session_state:
    st.session_state["assistant_running"] = False

if start_button and not st.session_state["assistant_running"]:
    threading.Thread(target=start_assistant, args=(input_device, output_device), daemon=True).start()
    st.session_state["assistant_running"] = True
    st.success("🟢 Assistant is now running!")

if stop_button and st.session_state["assistant_running"]:
    stop_assistant()
    st.session_state["assistant_running"] = False
    st.warning("🔴 Assistant has been stopped.")

# Live Transcription
st.header("📄 Live Transcription")
transcript_display = st.empty()

N_BRIGHT = 2
if st.session_state["assistant_running"]:
    while st.session_state["assistant_running"]:
        full_text = " ".join(current_transcript_lines)
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

        transcript_display.markdown(f'<div style="height: 300px; overflow-y: auto;">{html_output}</div>', unsafe_allow_html=True)
        time.sleep(1)
else:
    transcript_display.markdown("🔴 Assistant not running.")

st.divider()

# Upload Images
st.header("🖼️ Upload Lecture Images")
uploaded_files = st.file_uploader(
    "Upload lecture slides/images (PNG, JPG, JPEG)",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        if st.button(f"Summarize {uploaded_file.name}"):
            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                description = summarize_image(uploaded_file)
                image_summaries.append(description)
                uploaded_images.append(uploaded_file)
            st.success(f"✅ {uploaded_file.name} summarized!")

st.divider()

# Save Transcript
st.header("💾 Save Transcript")

def generate_title_from_transcript(text):
    try:
        excerpt = text[:300]
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": f"Generate a short academic title from this excerpt:\n\n{excerpt}"}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Title generation failed: {e}")
        return "Untitled Lecture"

if current_transcript_lines:
    full_text = "\n".join(current_transcript_lines)
    first_sentence = current_transcript_lines[0]
    quick_suggested_name = " ".join(first_sentence.split()[:5]) + "..." if len(first_sentence.split()) > 5 else first_sentence

    if st.button("🎯 Suggest Better Title"):
        smart_title = generate_title_from_transcript(full_text)
        st.session_state["smart_title"] = smart_title

    suggested_name = st.session_state.get("smart_title", quick_suggested_name)

    lecture_name = st.text_input("Lecture Name 📝", value=suggested_name)

    if st.button("💾 Final Save to MongoDB"):
        save_success = save_transcript_to_mongo(
            full_text,
            chosen_voice=st.session_state.get("chosen_voice", "Unknown"),
            lecture_name=lecture_name
        )
        if save_success:
            st.success("✅ Saved to MongoDB!")
        else:
            st.error("❌ Save failed.")
else:
    st.warning("⚠️ No transcript available yet.")

# Footer
st.markdown("""
<hr>
<p style="text-align: center; font-size: 14px; color: #888;">
    Built with ❤️ by Team HearSay | LA Hacks 2025
</p>
""", unsafe_allow_html=True)