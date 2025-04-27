import streamlit as st
from dotenv import load_dotenv
import pymongo
import sys
import os
import re
import json
from bson import ObjectId
from groq import Groq

# Load environment
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
MONGO_CONNECTION = os.getenv("MONGO_CONNECTION")

# Configure Groq
groq_client = Groq(api_key=api_key)
MODEL_NAME = "llama-3.3-70b-versatile"

# MongoDB setup
try:
    client = pymongo.MongoClient(MONGO_CONNECTION)
    db = client["materials"]
    collection = db["transcripts"]
except pymongo.errors.ConfigurationError:
    print("Invalid Mongo URI.")
    sys.exit(1)

# --- Flashcards ---

def show_flashcards(text):
    if st.button("🔮 Generate Flashcards"):
        with st.spinner('Generating flashcards...'):
            flashcards = generate_flashcards(text)
            st.session_state['flashcards'] = flashcards
            st.session_state['index'] = 0
            st.session_state['show_answer'] = False

    if 'flashcards' in st.session_state:
        flashcards = st.session_state['flashcards']
        index = st.session_state['index']
        show_answer = st.session_state.get('show_answer', False)

        if flashcards:
            question, answer = flashcards[index]
            st.markdown(f"### Q: {question}")
            if st.button("🔄 Flip Answer"):
                st.session_state['show_answer'] = not show_answer

            if show_answer:
                st.markdown(f"**A:** {answer}")

            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                if st.button("⬅️ Previous"):
                    st.session_state['index'] = (index - 1) % len(flashcards)
                    st.session_state['show_answer'] = False
            with col2:
                if st.button("➡️ Next"):
                    st.session_state['index'] = (index + 1) % len(flashcards)
                    st.session_state['show_answer'] = False

def generate_flashcards(transcript):
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": f"Create 5 flashcards (Q&A format only) from this lecture in JSON format, where the flashcards are dictionaries in a list, and the question and answer are keys, Q and A:\n\n{transcript}"}
        ]
    )
    flashcards_json = json.loads(re.sub(r"```(\w+)?\n?", "", response.choices[0].message.content).strip())

    flashcards = [(card["Q"].strip(), card["A"].strip()) for card in flashcards_json]
    return flashcards

# --- Summary ---

def show_summary(transcript):
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": f"Summarize this lecture in 500 words in Markdown, using bullet points. List 3 key terms and 3 key learnings:\n\n{transcript}"}
        ]
    )
    st.markdown(response.choices[0].message.content)

# --- Display Items ---

def display_items():
    items = collection.find().sort("timestamp", -1)  # Newest first
    st.title("📚 Lecture Notes")

    for item in items:
        st.markdown(f"""
            <a href="?page=lecture&id={item['_id']}&tab=overview" style="text-decoration: none;">
                <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                    <h3>📖 {item['name']}</h3>
                    <p><strong>🕒 Time:</strong> {item['timestamp']}</p>
                    <div style="max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        <p><strong>📝 Transcript:</strong> {item['transcript'][:150]}...</p>
                    </div>
                </div>
            </a>
        """, unsafe_allow_html=True)

# --- Display Lecture Details ---

def display_lecture_details():
    params = st.query_params

    if "id" in params:
        lecture_id = params["id"]
        item = collection.find_one({"_id": ObjectId(lecture_id)})

        if not item:
            st.error("Lecture not found.")
            return
        
        tab = st.sidebar.radio("Navigate", ["Full Transcription", "Flashcards", "Summary"])
        st.query_params.tab = tab.lower().replace(" ", "")

        if st.button("⬅️ Back to All Lectures"):
            st.query_params.clear()
            st.rerun()

        if tab == "Full Transcription":
            st.title(f"📖 {item['name']}")
            st.write(f"**🕒 Time:** {item['timestamp']}")
            st.write("### 📝 Full Transcript:")
            st.write(item['transcript'])

            if 'uploaded_images_base64' in item and item['uploaded_images_base64']:
                st.divider()
                st.subheader("🖼️ Uploaded Lecture Images")

                for idx, (img_b64, summary) in enumerate(zip(item['uploaded_images_base64'], item.get('image_summaries', [])), start=1):
                    st.image(f"data:image/png;base64,{img_b64}", caption=f"Lecture Image {idx}", use_column_width=True)
                    st.markdown(f"**Summary for Image {idx}:** {summary}")


        elif tab == "Flashcards":
            st.title(f"🎴 Flashcards for {item['name']}")
            show_flashcards(item['transcript'])

        elif tab == "Summary":
            st.title(f"📝 Summary: {item['name']}")
            show_summary(item['transcript'])

    else:
        st.error("No lecture ID provided.")

# --- Main Logic ---

def main():
    params = st.query_params
    if "page" in params and params["page"] == "lecture":
        display_lecture_details()
    else:
        display_items()

if __name__ == "__main__":
    main()