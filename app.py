import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
import sys

st.set_page_config(
    page_title="HearSay - Real-Time AI Assistant",
    page_icon="🦻",
    layout="wide"
)

st.image("assets/HearSay.gif")

# Define Pages
assistant_home = st.Page("pages/assistant_home.py", title="Assistant Home", icon="🎙️")
lectures = st.Page("pages/lectures.py", title="Lectures", icon="📚")

# Setup Navigation
pg = st.navigation([assistant_home, lectures])

# Run
pg.run()