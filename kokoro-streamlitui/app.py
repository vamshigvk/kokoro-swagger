import streamlit as st
import fitz  # PyMuPDF
import openai
import requests
import os
from io import BytesIO

# Streamlit UI Configuration
st.set_page_config(page_title="Audiobook & Podcast Generator", layout="wide")

# Sidebar Navigation
page = st.sidebar.selectbox("Navigation", ["Summary & Audiobook", "Podcast"])

def extract_text_from_pdf(pdf_file):
    """Extract text from a given PDF file."""
    try:
        print("Extracting text from PDF...")
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        print("Text extraction successful.")
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

def generate_summary(text, size):
    """Generate a summary using OpenAI's GPT model."""
    try:
        print("Generating summary...")
        summary_size_dict = {"small": 4, "medium": 10, "large": 20}
        prompt = (f"""Summarize the following text in {summary_size_dict[size]} lines for a text-to-audio model. "
                   "Ensure it has proper modulation, English punctuations. "
                   "Also, at the start include: 'You are listening to Boardroom Audio Assistant Luna! "
                   "Let me read out the summary of your document: \n' \n{text}""")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}]
        )
        print("Summary generated successfully.")
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return ""

def generate_audio(text, voice):
    """Generate an audio file from text using an external service."""
    try:
        print("Requesting audio generation...")
        response = requests.post("http://localhost:8080/generate_audio/", data={"text": text, "voice": voice})
        if response.status_code == 200:
            print("Audio generation successful.")
            return BytesIO(response.content)
        else:
            print(f"Audio generation failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None

if page == "Summary & Audiobook":
    st.title("📖 Summary & Audiobook")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📂 Upload PDF Document", type=["pdf"], help="Upload a PDF file for summarization and audiobook generation.")
    st.markdown("---")
    
    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            summary_size = st.selectbox("📏 *Select Summary Size*", ["small", "medium", "large"])
        with col2:
            voice_selection = st.selectbox("🎤 *Select Voice*", ["af_heart", "af_sarah", "a_bella", "af_sky"])
        with col3:
            generate_button = st.button("🚀 Generate Summary and Audiobook")

    if uploaded_file and generate_button:
        pdf_text = extract_text_from_pdf(uploaded_file)
        summary = generate_summary(pdf_text, summary_size)
        
        st.markdown("---")
        st.subheader("📜 Generated Summary:")
        st.write(summary)
        
        audio_file = generate_audio(summary, voice_selection)
        if audio_file:
            st.subheader("🔊 Audio Summary:")
            st.audio(audio_file, format='audio/wav')
        else:
            st.error("⚠️ Failed to generate audio.")

elif page == "Podcast":
    st.title("🎙️ Podcast")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📂 Upload PDF Document", type=["pdf"], help="Upload a PDF file to generate a podcast.")
    
    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            female_voice = st.selectbox("👩 *Select Female Voice*", ["af_alloy", "af_aoede", "af_bella", "af_heart", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky"])
        with col2:
            male_voice = st.selectbox("👨 *Select Male Voice*", ["am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa"])
        with col3:
            generate_podcast = st.button("🎤 Generate Podcast")
        
        if uploaded_file and generate_podcast:
            pdf_text = extract_text_from_pdf(uploaded_file)
            try:
                print("Requesting podcast generation...")
                response = requests.post("http://localhost:8080/generate_podcast/", data={"script_texts": pdf_text, "speaker1": female_voice, "speaker2": male_voice})
                
                if response.status_code == 200:
                    print("Podcast generated successfully.")
                    st.subheader("🔊 Generated Podcast:")
                    st.audio(BytesIO(response.content), format='audio/wav')
                else:
                    print(f"Podcast generation failed: {response.text}")
                    st.error("⚠️ Failed to generate podcast.")
            except Exception as e:
                print(f"Error generating podcast: {e}")
                st.error("⚠️ An error occurred while generating the podcast.")
