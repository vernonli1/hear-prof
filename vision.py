# vision_app.py
import base64
import os
import streamlit as st
from groq import Groq
import config  # assumes your API key is stored as GROQ_API_KEY

from PIL import Image
import io

def encode_image_to_base64(uploaded_file):
    """Reads an uploaded image file, resizes if necessary, and encodes it to base64."""
    image = Image.open(uploaded_file)

    # Check size — if any dimension > 1024px, resize it proportionally
    max_dimension = max(image.size)
    if max_dimension > 1024:
        scale = 1024 / max_dimension
        new_size = (int(image.size[0] * scale), int(image.size[1] * scale))
        image = image.resize(new_size)
        st.warning(f"Image was too large and has been resized to {new_size}")

    # Save resized image to a BytesIO buffer
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Always re-save as PNG to be safe
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def describe_image(base64_image, file_type, prompt):
    """Calls Groq Vision API to describe the image."""
    client = Groq(api_key=config.GROQ_API_KEY)
    chat_completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{file_type};base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        temperature=0.7,
        max_tokens=1024,  # <-- CORRECT key
        top_p=1,
        stream=False,
    )
    return chat_completion.choices[0].message.content

def main():
    st.set_page_config(page_title="Groq Vision - Image Describer", layout="centered")
    st.title("🖼️ Groq Vision Image Describer")
    st.write("Upload one or more images and get a description using Groq's Vision model.")

    # Prompt input
    prompt = st.text_input("Prompt to send to the model", value="Describe this image in detail.")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload image(s) (PNG, JPG, JPEG)", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

    save_outputs = st.checkbox("Save outputs as .txt files", value=True)
    output_dir = "outputs"
    if save_outputs and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if uploaded_files:
        if st.button("Analyze Images"):
            for uploaded_file in uploaded_files:
                try:
                    # Encode and get file type
                    file_type = uploaded_file.type
                    base64_img = encode_image_to_base64(uploaded_file)

                    # Call Vision Model
                    with st.spinner(f"Analyzing {uploaded_file.name}..."):
                        description = describe_image(base64_img, file_type, prompt)

                    # Display results
                    st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}")
                    with st.expander(f"See Description for {uploaded_file.name}"):
                        st.write(description)

                    # Save outputs
                    if save_outputs:
                        output_path = os.path.join(output_dir, f"{uploaded_file.name}_description.txt")
                        with open(output_path, "w") as f:
                            f.write(description)
                        st.success(f"Saved: {output_path}")

                except Exception as e:
                    st.error(f"Error analyzing {uploaded_file.name}: {e}")
    else:
        st.info("Please upload image files above.")

if __name__ == "__main__":
    main()