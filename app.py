import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
import sys


# Define the pages
main_page = st.Page("pages/transcriptions.py", title="Main Page", icon="🎈")
lesson_summaries = st.Page("pages/summaries.py", title="Summaries", icon="❄️")

# Set up navigation
pg = st.navigation([main_page, lesson_summaries])

# Run the selected page
pg.run()