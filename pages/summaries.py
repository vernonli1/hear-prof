import google.generativeai as genai
import os
import streamlit as st
from dotenv import load_dotenv

# Load API key securely
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

st.markdown("# Summarize ❄️")
st.sidebar.header("Summarize ❄️")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')  # or 'gemini-pro'

# Process lecture content
lecture_text = """
Today we'll discuss cellular respiration. This is the process by which cells convert 
glucose into ATP, the energy currency of the cell. There are three main stages:
1. Glycolysis - occurs in the cytoplasm, breaks glucose into pyruvate
2. Krebs cycle - occurs in mitochondria, produces electron carriers
3. Electron transport chain - creates ATP through oxidative phosphorylation

Remember that aerobic respiration requires oxygen, while anaerobic respiration 
produces lactic acid. The complete process yields about 36-38 ATP per glucose molecule.
"""

# Generate summary
response = model.generate_content(
    f"Summarize this lecture in 500 words using bullet points and list key terms:\n\n{lecture_text}"
)
st.markdown(response.text)

# Generate flashcards (optional)

if st.button("🔮 Generate Flashcards"):
    if lecture_text.strip() == "":
        st.warning("Please paste lecture content first.")
    else:
        with st.spinner('Generating flashcards...'):
            # Generate flashcards from Gemini
            flashcards_response = model.generate_content(
                f"Create 5 flashcards (Q&A format only) from this lecture:\n\n{lecture_text}"
            )

            flashcards_text = flashcards_response.text
            flashcards_list = flashcards_text.strip().split("\n\n")

            flashcards = []
            for card in flashcards_list:
                lines = card.split("\n")
                if len(lines) >= 2:
                    question = lines[0].replace("Q:", "").strip()
                    answer = lines[1].replace("A:", "").strip()
                    flashcards.append((question, answer))

            # Save into Session State
            st.session_state['flashcards'] = flashcards
            st.session_state['index'] = 0
            st.session_state['show_answer'] = False
            st.success("Flashcards ready! Start flipping ⬇️")

# Display Flashcards
if 'flashcards' in st.session_state and len(st.session_state['flashcards']) > 0:
    current_index = st.session_state['index']
    question, answer = st.session_state['flashcards'][current_index]

    st.markdown(f"### Flashcard {current_index + 1} / {len(st.session_state['flashcards'])}")
    if not st.session_state['show_answer']:
        st.info(f"🧠 **Question:** {question}")
    else:
        st.success(f"✅ **Answer:** {answer}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Flip Card"):
            st.session_state['show_answer'] = not st.session_state['show_answer']

    with col2:
        if st.button("➡️ Next Card"):
            if st.session_state['index'] < len(st.session_state['flashcards']) - 1:
                st.session_state['index'] += 1
                st.session_state['show_answer'] = False
            else:
                st.success("You've reached the end of flashcards! 🎉")
