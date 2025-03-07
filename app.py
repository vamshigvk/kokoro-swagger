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
import os

# Get the current working directory
current_dir = os.getcwd()
# Define the cache folder inside the current directory
hf_cache_dir = os.path.join(current_dir, "huggingface")
# Set HF_HOME environment variable dynamically
os.environ["HF_HOME"] = hf_cache_dir
print(f"HF_HOME is set to: {os.environ['HF_HOME']}")

# Initialize FastAPI
app = FastAPI()

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Kokoro pipeline with error handling
try:
    pipeline = KPipeline(lang_code='a')
except Exception as e:
    logging.error(f"Failed to initialize Kokoro pipeline: {str(e)}")
    raise RuntimeError("KPipeline initialization failed.")

# Define an Enum class for available voices
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
    output_dir = "generated_audio"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the output directory exists

    gs_list, ps_list = [], []
    all_audio_data = []
    sample_rate = 24000  # Fixed sample rate

    try:
        generator = pipeline(
            text, voice=voice.value, speed=1, split_pattern=r'\n+'
        )
    except Exception as e:
        logging.error(f"Pipeline processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error in text-to-speech processing.")

    try:
        for gs, ps, audio in generator:
            gs_list.append(gs)
            ps_list.append(ps)
            all_audio_data.append(audio)

        if not all_audio_data:
            raise ValueError("No audio was generated.")

        # Concatenate all audio segments into a single file
        merged_audio = np.concatenate(all_audio_data, axis=0)
        merged_audio_path = os.path.join(output_dir, "merged_audio.wav")

        # Ensure audio is not empty before writing
        if merged_audio.size == 0:
            raise RuntimeError("Merged audio is empty, file not created.")

        # Save the merged audio file
        sf.write(merged_audio_path, merged_audio, sample_rate)

        # Validate that the file was successfully created
        if not os.path.exists(merged_audio_path):
            raise RuntimeError(f"File at path {merged_audio_path} does not exist.")

        # Base64 encode headers to avoid Unicode encoding issues
        gs_encoded = base64.b64encode(",".join(gs_list).encode("utf-8")).decode("utf-8")
        ps_encoded = base64.b64encode(",".join(ps_list).encode("utf-8")).decode("utf-8")

        # Create response with headers
        response = FileResponse(
            merged_audio_path, filename="merged_audio.wav", media_type="audio/wav"
        )
        response.headers["X-Graphemes"] = gs_encoded
        response.headers["X-Phonemes"] = ps_encoded

        return response

    except ValueError as ve:
        logging.error(f"Audio generation failed: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))

    except RuntimeError as re:
        logging.error(f"Runtime error: {str(re)}")
        raise HTTPException(status_code=500, detail=str(re))

    except Exception as e:
        logging.error(f"Unexpected error during processing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during processing.")
