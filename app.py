import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
import sys
st.set_page_config(
    page_title="HearSay",
    page_icon="🔊",
)


st.image("assets/HearSay.gif")

# Define the pages
main_page = st.Page("pages/transcriptions.py", title="Main Page", icon="🎈")
lectures = st.Page("pages/lectures.py", title="Lectures", icon="📚")

# Set up navigation
pg = st.navigation([main_page, lectures])

# Run the selected page
pg.run()