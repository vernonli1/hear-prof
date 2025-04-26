import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load API key securely
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

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
print(response.text)

# Generate flashcards (optional)
flashcards = model.generate_content(
    f"Create 5 flashcards (Q&A format) from this lecture:\n\n{lecture_text}"
)
print("\nFlashcards:\n", flashcards.text)
