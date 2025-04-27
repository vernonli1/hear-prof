import streamlit as st
from dotenv import load_dotenv
import pymongo
import sys
import os
import re
import json
from bson import ObjectId
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key securely
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

load_dotenv()

# Database setup
MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")
try:
    client = pymongo.MongoClient(MONGO_CONNECTION)
    db = client["materials"]     # choose your database
    collection = db["transcripts"]  # choose your collection
# return a friendly error if a URI error is thrown 
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
    sys.exit(1)


def show_flashcards(text):
    # Flashcard Button
    if st.button("🔮 Refresh Flashcards"):
        with st.spinner('Generating flashcards...'):
            flashcards = generate_flashcards(text)
            # Save into Session State
            st.session_state['flashcards'] = flashcards
            st.session_state['index'] = 0
            st.session_state['show_answer'] = False


    # Show Flashcards
    if 'flashcards' in st.session_state:
        flashcards = st.session_state['flashcards']
        index = st.session_state['index']
        show_answer = st.session_state['show_answer']

        if flashcards:
            question, answer = flashcards[index]
            if not show_answer:
                st.markdown(f"### Q: {question}")

            else:
                st.markdown(f"### A: {answer}")

            col1, col2, col3 = st.columns(3)

            with col1:
                prev_clicked = st.button("⬅️ Previous")
            with col2:
                flip_clicked = st.button("🔄 Flip")
            with col3:
                next_clicked = st.button("➡️ Next")

            if flip_clicked:
                st.session_state['show_answer'] = not show_answer

            elif next_clicked:
                st.session_state['show_answer'] = False
                st.session_state['index'] = (index + 1) % len(flashcards)

            elif prev_clicked:
                st.session_state['show_answer'] = False
                st.session_state['index'] = (index - 1) % len(flashcards)


def generate_flashcards(transcript):
    flashcards_response = model.generate_content(
        f"Create 5 flashcards (Q&A format only) from this lecture in JSON format, where the flashcards are dictionaries in a list, and the question and answer are keys, Q and A, in a dictionary:\n\n{transcript}"
    )
    # parse out AI response
    flashcards_json = json.loads(re.sub(r"```(\w+)?\n?", "", flashcards_response.text))

    flashcards = []
    for card in flashcards_json:
        question = card["Q"].strip()
        answer = card["A"].strip()

        flashcards.append((question, answer))
    return flashcards

def show_summary(transcript):
    ai_summary = model.generate_content(
        f"Summarize this lecture in 500 words in Markdown, concisely and in a fun way, using bullet points and list 3 key terms and 3 key learnings:\n\n{transcript}"
    )
    st.markdown(ai_summary.text)

# Define a function to display items in Streamlit
def display_items():
    items = collection.find()
    st.title("Lecture Notes")
    
    for item in items:
        # Display each item in a box
        st.markdown(f"""
            <a href="?page=lecture&id={item["_id"]}&tab=overview" style="text-decoration: none;">
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                <h3>Lecture: {item['name']}</h3>
                <p><strong>Time:</strong> {item['timestamp']}</p>
                <div style="max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    <p><strong>Transcript:</strong> {item['transcript'][:150]}...</p>  <!-- Limits to 150 characters -->
                </div>
            </div>
        """, unsafe_allow_html=True)


# Define a function to display the lecture details based on the ID
def display_lecture_details():
    params = st.query_params
    
    if "id" in params:
        lecture_id = params["id"]
        item = collection.find_one({"_id": ObjectId(lecture_id)})  # Fetch the item by ID
        
        tab = st.sidebar.radio("Go to", ["Full Lesson Transcription", "Flashcards", "Lesson Summary"])

        # Update URL when tab changes
        st.query_params.tab = tab.lower().replace(" ", "")

        if st.button("Back to All Lectures"):
            st.query_params.clear()
            st.rerun()

        if tab == "Flashcards":
            # Example: Generate simple flashcards
            show_flashcards(item['transcript'])
        elif tab == "Lesson Summary":
            st.title(f"Lesson Summary: {item['name']}")
            show_summary(item['transcript'])

        if item and tab != "Lesson Summary":
            st.title(f"Lecture: {item['name']}")
            st.write(f"**Time:** {item['timestamp']}")
            st.write(f"**Transcript:** {item['transcript']}")
        elif not item:
            st.error("Lecture not found.")
        else:
            pass
    else:
        st.error("No lecture ID provided.")

# Main function to decide which page to display based on query parameters
def main():
    params = st.query_params

    # Check if the page is for a specific lecture
    if "page" in params and params["page"] == "lecture":
        
        display_lecture_details()
    else:
        display_items()

if __name__ == "__main__":
    main()