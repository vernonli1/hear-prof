import streamlit as st
import threading
from assistant_backend import start_assistant, current_transcript
from streamlit_autorefresh import st_autorefresh

st.title("🎙️ Real-Time Classroom Assistant")

if "assistant_running" not in st.session_state:
    st.session_state.assistant_running = False

if st.button("🚀 Start Assistant") and not st.session_state.assistant_running:
    threading.Thread(target=start_assistant, daemon=True).start()
    st.session_state.assistant_running = True
    st.success("Assistant started!")

st.subheader("Live Transcription")
transcript_area = st.empty()

# Autorefresh every 1000 ms
count = st_autorefresh(interval=1000, limit=None, key="transcription_refresh")

if st.session_state.assistant_running:
    transcript_area.markdown(current_transcript.replace("\n", "<br>"), unsafe_allow_html=True)