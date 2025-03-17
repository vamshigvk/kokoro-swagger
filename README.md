### kokoro swagger with streamlit to generate audio files and podcasts on your documents
Note:
- set your openai key from cmd using in Mac:
```$export OPENAI_API_KEY="your-api-key-here"
$source ~/.zshrc  # For Zsh
$source ~/.bashrc  # For Bash
```
- Loading the Key in Python:
```
import os
openai_api_key = os.getenv("OPENAI_API_KEY")
print(openai_api_key)  # Should print your API key
```
- Run swagger from cmd:
```
uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```
- Run Streamlit from cmd:
```
streamlit run app.py
```
