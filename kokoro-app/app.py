import ast
import base64
import logging
import os
import numpy as np
import soundfile as sf
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from enum import Enum
from kokoro import KPipeline
import uvicorn
import openai

# Set up Hugging Face cache directory
current_dir = os.getcwd()
hf_cache_dir = os.path.join(current_dir, "huggingface")
os.environ["HF_HOME"] = hf_cache_dir
print(f"HF_HOME is set to: {os.environ['HF_HOME']}")

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Kokoro pipeline with error handling
try:
    print("Initializing Kokoro pipeline...")
    pipeline = KPipeline(lang_code='a')
    print("Kokoro pipeline initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Kokoro pipeline: {str(e)}")
    raise RuntimeError("KPipeline initialization failed.")

# Define Enum for available voices
class Voices(str, Enum):
    af_alloy = "af_alloy"
    af_aoede = "af_aoede"
    af_bella = "af_bella"
    af_heart = "af_heart"
    af_jessica = "af_jessica"
    af_kore = "af_kore"
    af_nicole = "af_nicole"
    af_nova = "af_nova"
    af_river = "af_river"
    af_sarah = "af_sarah"
    af_sky = "af_sky"
    am_adam = "am_adam"
    am_echo = "am_echo"
    am_eric = "am_eric"
    am_fenrir = "am_fenrir"
    am_liam = "am_liam"
    am_michael = "am_michael"
    am_onyx = "am_onyx"
    am_puck = "am_puck"
    am_santa = "am_santa"

# Request model for API documentation
class AudioRequest(BaseModel):
    text: str
    voice: Voices

@app.post("/generate_audio/")
def generate_audio(text: str = Form(...), voice: Voices = Form(...)):
    """
    Endpoint to generate audio from text using the Kokoro pipeline.
    """
    print(f"Received request to generate audio: text='{text}', voice='{voice}'")
    output_dir = "generated_audio"
    os.makedirs(output_dir, exist_ok=True)

    gs_list, ps_list = [], []
    all_audio_data = []
    sample_rate = 24000  # Fixed sample rate

    try:
        generator = pipeline(text, voice=voice.value, speed=1, split_pattern=r'\n+')
        
        for gs, ps, audio in generator:
            gs_list.append(gs)
            ps_list.append(ps)
            all_audio_data.append(audio)
        
        if not all_audio_data:
            raise ValueError("No audio was generated.")

        return save_and_respond(all_audio_data, "merged_audio.wav", sample_rate, gs_list, ps_list)
    
    except Exception as e:
        logging.error(f"Error in audio generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during processing.")

def save_and_respond(all_audio_data, filename, sample_rate, gs_list=None, ps_list=None):
    """
    Helper function to save generated audio and return it as a response.
    """
    print(f"Saving generated audio to {filename}")
    
    if not all_audio_data:
        raise HTTPException(status_code=400, detail="No audio generated.")
    
    merged_audio = np.concatenate(all_audio_data, axis=0)
    output_dir = "generated_audio"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    sf.write(file_path, merged_audio, sample_rate)
    response = FileResponse(file_path, filename=filename, media_type="audio/wav")
    
    if gs_list and ps_list:
        response.headers["X-Graphemes"] = base64.b64encode(",".join(gs_list).encode("utf-8")).decode("utf-8")
        response.headers["X-Phonemes"] = base64.b64encode(",".join(ps_list).encode("utf-8")).decode("utf-8")
    
    return response

def generate_transcript(script_text, voice1, voice2):
    """
    Generate a natural-sounding podcast script using GPT-4o.
    """
    print("Generating podcast transcript...")
    try:
        prompt = f"""TASK:\n- Create a natural-sounding podcast conversation based on the following SCRIPT.\n- Use human-like elements such as fillers, emotions, and natural flow.\n- Ensure that "Emma" and "Ryan" sound distinct with voice names {voice1} and {voice2}.
        SCRIPT: {script_text}
        OUTPUT_FORMAT: [("Hello everyone! Welcome to our podcast!", "voice1"),\n("Today, we will discuss AI innovations.", "voice2"),\n("Stay tuned for more updates!", "voice1")]
        OUTPUT_GUIDELINES:\n- Strictly print the output in OUTPUT_FORMAT\n- No words or characters before or after OUTPUT_FORMAT"""
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a podcast host."},
                {"role": "user", "content": prompt}
            ]
        )
        transcript = response["choices"][0]["message"]["content"].strip()
        print("Generated transcript:", transcript)
        return transcript
    except Exception as e:
        logging.error(f"Error generating transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in generating podcast script.")

@app.post("/generate_podcast/")
def generate_podcast(
    script_texts: str = Form(...), 
    speaker1: Voices = Form(...), 
    speaker2: Voices = Form(...)
):
    """
    Endpoint to generate a podcast conversation with two speakers.
    """
    print(f"Received request to generate podcast: speaker1='{speaker1}', speaker2='{speaker2}'")
    try:
        transcript = generate_transcript(script_texts, speaker1.value, speaker2.value)
        transcript_list = ast.literal_eval(transcript)
        
        all_audio_data = []
        sample_rate = 24000
        
        for text, voice in transcript_list:
            generator = pipeline(text, voice=voice, speed=1, split_pattern=r'\n+')
            for _, _, audio in generator:
                all_audio_data.append(audio)
        
        return save_and_respond(all_audio_data, "podcast.wav", sample_rate)
    except Exception as e:
        logging.error(f"Error generating podcast: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during podcast generation.")

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8080)