import os
import json
from groq import Groq
from dotenv import load_dotenv
from langdetect import detect, LangDetectException

# --- 1. REMOVED ALL ELEVENLABS IMPORTS TO FIX THE CRASH ---
# We will only use the reliable gTTS library.
from gtts import gTTS

load_dotenv()

# --- 2. INITIALIZE API CLIENTS ---
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Core Service Functions (Unchanged and correct) ---

def detect_language(text: str) -> str:
    """Detects the language of text, returns ISO 639-1 code (e.g., 'en', 'hi')."""
    try:
        if text.lower().strip() in ["yes", "ok", "no", "thanks", "hello", "hi"]: return "en"
        return detect(text)
    except LangDetectException:
        print("Language detection failed, defaulting to English.")
        return "en"

def translate_text(text: str, target_language: str = "en") -> str:
    """Translates text to a target language using a fast LLM."""
    source_language = detect_language(text)
    if source_language == target_language:
        return text
    translation_prompt = f"Translate the following text to {target_language}. Respond with ONLY the translated text.\n\nText: \"{text}\""
    try:
        translated_text = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": translation_prompt}]
        ).choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

def get_llm_response(prompt):
    """Gets a standard text response from the LLM."""
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "I'm sorry, I'm having trouble thinking right now."

def get_json_response_from_llm(prompt):
    """Gets a guaranteed JSON response from the LLM using Groq's JSON Mode."""
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that always outputs in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"JSON LLM Error: {e}")
        return "{}"


# --- THE DEFINITIVE, RELIABLE text_to_speech FUNCTION (gTTS ONLY) ---
def text_to_speech(text: str, call_sid: str, lang_code: str = 'en'):
    """
    Converts text to audio using the reliable gTTS library.
    This version bypasses the ElevenLabs error to ensure the demo works.
    """
    filepath = f"assets/{call_sid}.mp3"
    base_url = os.getenv("BASE_URL")
    
    try:
        print(f"Generating '{lang_code}' audio with gTTS...")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filepath)
        print(f"gTTS audio generated successfully.")
    except Exception as gtts_e:
        # Final fallback if even gTTS fails
        print(f"gTTS failed: {gtts_e}. Creating generic error audio.")
        tts = gTTS(text="I have an answer, but I am having trouble speaking right now.", lang='en')
        tts.save(filepath)

    return f"{base_url}/{filepath}"