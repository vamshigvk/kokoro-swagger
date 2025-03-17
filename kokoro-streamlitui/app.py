import streamlit as st
import fitz  # PyMuPDF
import openai
import requests
import os
from io import BytesIO

# Set OpenAI API key
openai.api_key = "yourtoken"

# Streamlit UI
st.set_page_config(page_title="Audiobook", layout="wide")

# Sidebar Navigation
# st.sidebar.markdown("## Navigation", unsafe_allow_html=True)
# st.sidebar.markdown("---")
page = st.sidebar.selectbox("Navigation", ["Summary & Audiobook", "Podcast"])

if page == "Summary & Audiobook":
    st.title("📖 Summary & Audiobook")
    st.markdown("---")
    
    # File Uploader
    uploaded_file = st.file_uploader("📂 Upload PDF Document", type=["pdf"], help="Upload a PDF file for summarization and audiobook generation.")
    st.markdown("---")
    
    # Summary size and voice selection in columns
    if uploaded_file:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            summary_size = st.selectbox("📏 *Select Summary Size*", ["small", "medium", "large"])
        with col2:
            voice_selection = st.selectbox("🎤 *Select Voice*", ["af_heart", "af_sarah", "a_bella", "af_sky"])
        with col3:
            generate_button = st.button("🚀 Generate Summary and Audiobook", use_container_width=True)
    
    def extract_text_from_pdf(pdf_file):
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        return text
    
    def generate_summary(text, size):
        prompt = f"""Summarize the following text in {size} lines for a text to audio model. ensure it has right modulation, english puncuations. Also, at the start of the statement include this "You are listening to Boardroom Audio assistant Luna! Let me read out the Summary of your document: \n :" \n{text} """
        with st.spinner("🔄 Generating summary..."):
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
        return response["choices"][0]["message"]["content"].strip()

    def generate_audio(summary, voice):
        with st.spinner("🎵 Generating audio..."):
            response = requests.post("http://localhost:8080/generate_audio/", data={"text": summary, "voice": voice})

        st.markdown("---")
        
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            return response.text
    
    if uploaded_file and generate_button:
        pdf_text = extract_text_from_pdf(uploaded_file)
        summary_size_dict = {"small": 4, "medium": 10, "large": 20}
        summary = generate_summary(pdf_text, summary_size_dict[summary_size])    
        st.markdown("---")
        st.subheader("📜 Generated Summary:")
        st.write(summary)
        
        audio_file = generate_audio(summary, voice_selection)
        if isinstance(audio_file, BytesIO):
            st.subheader("🔊 Audio Summary:")
            st.audio(audio_file, format='audio/wav')
        else:
            st.error("⚠️ Failed to generate audio.")

elif page == "Podcast":
    st.title("🎙️ Podcast")
    st.markdown("---")
    
    # Podcast Player
    st.subheader("🎧 Podcast Player")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Play Podcast 1"):
            podcast_path1 = "static_podcasts/podcast_audio1.wav"
            if os.path.exists(podcast_path1):
                st.audio(podcast_path1, format='audio/wav')
            else:
                st.error("⚠️ Podcast file not found.")
    
    with col2:
        if st.button("▶️ Play Podcast 2"):
            podcast_path2 = "static_podcasts/podcast_audio2.wav"
            if os.path.exists(podcast_path2):
                st.audio(podcast_path2, format='audio/wav')
            else:
                st.error("⚠️ Podcast file not found.")