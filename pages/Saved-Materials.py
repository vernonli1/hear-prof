import streamlit as st
from dotenv import load_dotenv
import pymongo
import os
import sys
import json
import re
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

# --- Helper: Generate Flashcards from Transcript ---
def generate_flashcards(transcript):
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": f"Create 5 flashcards (Q&A format only) from this lecture in JSON. Each card must have 'Q' and 'A' keys:\n\n{transcript}"}
        ]
    )
    cleaned = re.sub(r"```(\w+)?\n?", "", response.choices[0].message.content).strip()
    flashcards_json = json.loads(cleaned)
    return [(card["Q"].strip(), card["A"].strip()) for card in flashcards_json]

# --- Helper: Summarize Lecture Transcript ---
def summarize_lecture(transcript):
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": f"Summarize this lecture in 500 words using Markdown bullet points. List 3 key terms and 3 key learnings:\n\n{transcript}"}
        ]
    )
    return response.choices[0].message.content

# --- Flashcard Viewer ---
def flashcard_viewer(transcript):
    if st.button("🔮 Generate Flashcards"):
        with st.spinner('Creating flashcards...'):
            flashcards = generate_flashcards(transcript)
            st.session_state['flashcards'] = flashcards
            st.session_state['index'] = 0
            st.session_state['show_answer'] = False

    if 'flashcards' in st.session_state:
        flashcards = st.session_state['flashcards']
        index = st.session_state['index']
        show_answer = st.session_state.get('show_answer', False)

        if flashcards:
            question, answer = flashcards[index]

            st.markdown(f"### ❓ {question}")
            if st.button("🔄 Flip to Answer"):
                st.session_state['show_answer'] = not show_answer

            if show_answer:
                st.markdown(f"**✅ {answer}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Previous"):
                    st.session_state['index'] = (index - 1) % len(flashcards)
                    st.session_state['show_answer'] = False
            with col2:
                if st.button("➡️ Next"):
                    st.session_state['index'] = (index + 1) % len(flashcards)
                    st.session_state['show_answer'] = False

# --- Show All Lectures (Main Page) ---
def show_all_lectures():
    st.title("📚 Lecture Library")

    items = collection.find().sort("timestamp", -1)

    for item in items:
        with st.container():
            st.markdown(f"""
                <div style="border: 1px solid #333; padding: 20px; border-radius: 16px; margin-bottom: 20px; background-color: #1a1d26; transition: background-color 0.3s;">
                    <h3>📖 {item['name']}</h3>
                    <p><strong>🕒 {item['timestamp']}</strong></p>
                    <div style="overflow: hidden; text-overflow: ellipsis;">
                        <p>{item['transcript'][:150]}...</p>
                    </div>
                    <a href="?page=lecture&id={item['_id']}&tab=overview" style="text-decoration: none; color: #636efa;">🔗 View Details</a>
                </div>
            """, unsafe_allow_html=True)

# --- Show Individual Lecture (Detail View) ---
def show_lecture_detail():
    params = st.query_params

    if "id" in params:
        lecture_id = params["id"]
        item = collection.find_one({"_id": ObjectId(lecture_id)})

        if not item:
            st.error("Lecture not found.")
            return
        
        # Tabs Sidebar
        tab = st.sidebar.radio("Navigate", ["📖 Full Transcript", "🎴 Flashcards", "📝 Summary"])
        st.query_params.tab = tab.lower().replace(" ", "")

        if st.button("⬅️ Back to All Lectures"):
            st.query_params.clear()
            st.rerun()

        st.title(f"📖 {item['name']}")

        if tab == "📖 Full Transcript":
            st.subheader("📝 Full Transcript")
            st.write(f"**🕒 Time:** {item['timestamp']}")
            st.write(item['transcript'])

            if 'uploaded_images_base64' in item and item['uploaded_images_base64']:
                st.divider()
                st.subheader("🖼️ Uploaded Lecture Images")
                for idx, (img_b64, summary) in enumerate(zip(item['uploaded_images_base64'], item.get('image_summaries', [])), start=1):
                    st.image(f"data:image/png;base64,{img_b64}", caption=f"Lecture Image {idx}", use_column_width=True)
                    st.markdown(f"**Summary {idx}:** {summary}")

        elif tab == "🎴 Flashcards":
            st.subheader(f"🎴 Flashcards")
            flashcard_viewer(item['transcript'])

        elif tab == "📝 Summary":
            st.subheader("📝 Lecture Summary")
            st.markdown(summarize_lecture(item['transcript']))

    else:
        st.error("No lecture ID provided.")

# --- Main Logic ---
def main():
    params = st.query_params
    if "page" in params and params["page"] == "lecture":
        show_lecture_detail()
    else:
        show_all_lectures()

if __name__ == "__main__":
    main()