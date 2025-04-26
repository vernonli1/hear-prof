import streamlit as st
import pymongo
from dotenv import load_dotenv
import os
import sys

load_dotenv()

MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")

# define database
try:
    client = pymongo.MongoClient(MONGO_CONNECTION)
  
# return a friendly error if a URI error is thrown 
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
    sys.exit(1)

# Define the pages
main_page = st.Page("pages/transcriptions.py", title="Main Page", icon="🎈")
lesson_summaries = st.Page("pages/transcriptions.py", title="", icon="❄️")

# Set up navigation
pg = st.navigation([main_page])

# Run the selected page
pg.run()