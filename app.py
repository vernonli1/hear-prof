import streamlit as st
import os
from dotenv import load_dotenv

# Set up page config
st.set_page_config(
    page_title="HearSay - Home",
    page_icon="🏠",
    layout="wide"
)

# Load environment
load_dotenv()

# Inject custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    text-align: center; /* <--- ADD CENTER ALIGN TO EVERYTHING */
}
section[data-testid="stSidebar"] {
    background: rgba(14, 17, 23, 0.95);
    backdrop-filter: blur(8px);
}
h1, h2, h3, h4 {
    font-family: 'Poppins', sans-serif;
    text-align: center; /* <--- MAKE HEADERS CENTERED */
}
.stButton>button {
    background: linear-gradient(90deg, #636efa, #00c7b7);
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    color: white;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    background: linear-gradient(90deg, #00c7b7, #636efa);
    transform: scale(1.05);
}

/* Hero Section */
.hero-section {
    position: relative;
    text-align: center;
    padding: 6rem 2rem 4rem 2rem;
    background: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85));
    border-radius: 1rem;
    margin: auto; /* <--- CENTER HERO SECTION ITSELF */
    max-width: 900px; /* <--- LIMIT MAX WIDTH */
    margin-bottom: 3rem;
}
.hero-logo {
    width: 200px;
    opacity: 0.8;
    margin-bottom: 1.5rem;
}
.hero-title {
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 1rem;
}
.hero-subtitle {
    font-size: 1.4rem;
    font-weight: 400;
    color: #d1d1d1;
}

/* Explore Section */
.explore-section {
    margin: auto;
    max-width: 900px;
    padding: 2rem;
}
.card, .explore-tile {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 2rem;
    transition: all 0.3s ease;
    animation: fadeInSlide 0.6s ease forwards;
    opacity: 0;
    margin-bottom: 2rem;
}
.card:hover, .explore-tile:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
.explore-tile {
    text-align: center;
    font-size: 1.7rem;
    font-weight: 600;
    color: #ffffff;
    text-decoration: none;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 170px;
}
.explore-tile:hover {
    text-decoration: none;
    color: white;
}
@keyframes fadeInSlide {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

hr {
    margin-top: 3rem;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# --- Hero Section ---
# --- Hero Section ---
st.markdown('<div class="hero-section">', unsafe_allow_html=True)

with st.container():
    st.image("assets/HearSay.gif", width=70)

st.markdown("""
    <div class="hero-title">The next-generation real-time classroom assistant.</div>
    <div class="hero-subtitle">Transcribe. Translate. Focus.<br>Built for learning in the modern age.</div>
</div>
""", unsafe_allow_html=True)

# --- Explore Section ---
st.markdown("<div class='explore-section'>", unsafe_allow_html=True)
st.markdown("<h2 style='color: #636efa;'>🔍 Explore HearSay</h2>", unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("""
    <a href="/Live-Assistant" class="explore-tile">
        🎙️ Live Assistant
    </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <a href="/Saved-Materials" class="explore-tile">
        📚 Saved Materials
    </a>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- Footer ---
st.markdown("""
<p style="font-size: 14px; color: #888;">
    Built with ❤️ by Team HearSay | LA Hacks 2025
</p>
""", unsafe_allow_html=True)