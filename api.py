import os
import sys
import io
import time
import requests
from fastapi import FastAPI, Form, UploadFile, File, Response
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from pydantic import BaseModel
from dotenv import load_dotenv # Import load_dotenv first

# --- 1. CRITICAL: Load Environment Variables at the very top ---
# This ensures that all subsequent imports that rely on API keys will work correctly.
load_dotenv()

# --- 2. Now, import your application's core logic ---
from core.router import vaani_router
from core.services import text_to_speech, detect_language
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware

# --- Initialization ---
app = FastAPI()

# --- Enable CORS for Frontend Communication ---
# This is essential for your HTML/CSS/JS UI to connect to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Create assets directory to store generated audio files
os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Initialize API clients once to be reused across the application
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Pydantic Model for JSON requests from your custom web UI ---
class ChatRequest(BaseModel):
    query: str
    sid: str = "webapp_session" # Use a default session ID for the webapp

# --- Helper Functions ---

def send_whatsapp_message(from_number: str, to_number: str, message_body: str):
    """Sends a WhatsApp text message, automatically chunking if it's too long."""
    max_length = 1590
    if len(message_body) <= max_length:
        twilio_client.messages.create(body=message_body, from_=from_number, to=to_number)
    else:
        chunks = [message_body[i:i+max_length] for i in range(0, len(message_body), max_length)]
        for i, chunk in enumerate(chunks):
            part_indicator = f"({i+1}/{len(chunks)}) "
            twilio_client.messages.create(body=part_indicator + chunk, from_=from_number, to=to_number)

def transcribe_whatsapp_voice(audio_url: str) -> str:
    """Downloads a protected WhatsApp voice note and transcribes it using Groq."""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        audio_response = requests.get(audio_url, auth=(account_sid, auth_token))
        audio_response.raise_for_status()
        transcription = groq_client.audio.transcriptions.create(
            file=("whatsapp_voice.ogg", audio_response.content), model="whisper-large-v3",
        )
        return transcription.text
    except Exception as e:
        print(f"Error transcribing WhatsApp voice note: {e}")
        return ""

# --- API Endpoints ---

@app.post("/chat")
async def handle_chat(request: ChatRequest):
    """Handles requests from the custom HTML/CSS/JS chatbot UI."""
    if not request.query:
        return {"error": "No query provided."}
    
    try:
        response_text, agent_used = vaani_router(request.query, request.sid)
        
        response_lang_code = detect_language(response_text)
        audio_filename = f"{request.sid}_{int(time.time())}.mp3"
        audio_url = text_to_speech(response_text, audio_filename.split('.')[0], response_lang_code)
        
        return {"response_text": response_text, "agent_used": agent_used, "audio_url": audio_url}
    except Exception as e:
        print(f"!!! UNCAUGHT ERROR IN /chat ENDPOINT: {e}")
        # Also print the full traceback for detailed debugging
        import traceback
        traceback.print_exc()
        return {"error": "An unexpected error occurred on the backend. Check the server logs."}

@app.post("/transcribe-webaudio")
async def handle_transcribe_webaudio(audio_file: UploadFile = File(...)):
    """Handles voice command transcription for the custom UI."""
    if not audio_file: return {"error": "No audio file provided."}
    audio_data = await audio_file.read()
    transcription = groq_client.audio.transcriptions.create(
        file=("webaudio.wav", audio_data), model="whisper-large-v3",
    )
    return {"transcription": transcription.text}

@app.post("/handle-call")
async def handle_call():
    """Handles traditional voice calls."""
    response = VoiceResponse(); response.say("नमस्ते, वाणी में आपका स्वागत है। आप अपना सवाल पूछ सकते हैं।", language="hi-IN"); response.record(transcribe=True, transcribe_callback="/handle-transcription")
    return Response(content=str(response), media_type="application/xml")

@app.post("/handle-transcription")
async def handle_transcription(CallSid: str = Form(...), TranscriptionText: str = Form(...)):
    """Processes audio from a voice call and responds with a voice message."""
    response_text, agent_used = vaani_router(TranscriptionText, CallSid)
    response_lang_code = detect_language(response_text)
    audio_url = text_to_speech(response_text, CallSid, response_lang_code)
    with open("mission_control_log.txt", "w") as f: f.write(f"--- Voice Call ---\n...")
    response = VoiceResponse(); response.play(audio_url); response.hangup()
    return Response(content=str(response), media_type="application/xml")

@app.post("/handle-whatsapp")
async def handle_whatsapp(From: str = Form(...), Body: str = Form(None), MediaUrl0: str = Form(None), NumMedia: int = Form(...)):
    """Handles incoming WhatsApp messages, providing both text and voice responses."""
    user_input, input_type = "", "Unknown"
    if NumMedia > 0 and MediaUrl0:
        input_type = "Voice Note"; user_input = transcribe_whatsapp_voice(MediaUrl0)
    elif Body:
        input_type = "Text Message"; user_input = Body
    
    if not user_input:
        send_whatsapp_message(f'whatsapp:{os.getenv("TWILIO_WHATSAPP_NUMBER")}', From, "I'm sorry, I couldn't understand that.")
        return Response(status_code=204)

    response_text, agent_used = vaani_router(user_input, From)
    send_whatsapp_message(f'whatsapp:{os.getenv("TWILIO_WHATSAPP_NUMBER")}', From, response_text)
    
    response_lang_code = detect_language(response_text)
    audio_response_url = text_to_speech(response_text, From.replace('+', ''), response_lang_code)
    
    if audio_response_url:
        twilio_client.messages.create(from_=f'whatsapp:{os.getenv("TWILIO_WHATSAPP_NUMBER")}', to=From, media_url=[audio_response_url])
        
    with open("mission_control_log.txt", "w") as f: f.write(f"--- WhatsApp ---\n...")
    return Response(status_code=204)