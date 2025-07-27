import streamlit as st
import os
import time
import requests
from streamlit_mic_recorder import mic_recorder

# --- Core Application Imports ---
# These are imported only when needed to speed up the initial UI load.

st.set_page_config(page_title="VaaniVerse Demo Hub", layout="wide")

# --- Initialize Session State ---
# This is the core of the fix. We use explicit flags to control the app's flow.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_input_ready" not in st.session_state:
    st.session_state.user_input_ready = False
if "latest_user_query" not in st.session_state:
    st.session_state.latest_user_query = ""

# --- API Endpoint URL ---
BACKEND_URL = "http://localhost:8000"

# --- Main App Structure ---
st.title("VaaniVerse: Your AI Companion")

# Display chat history from the session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio_path" in message:
            st.audio(message["audio_path"])

# --- User Input Handling at the bottom of the page ---
st.markdown("---")

# Text Input Box
text_prompt = st.chat_input("Ask VaaniVerse anything...")
if text_prompt:
    # When user types and hits Enter, set the query and flag that input is ready
    st.session_state.latest_user_query = text_prompt
    st.session_state.user_input_ready = True

# Voice Input Button
voice_input = mic_recorder(
    start_prompt="Click to Record 🎤", stop_prompt="Click to Stop ⏹️", key='recorder'
)
if voice_input:
    st.info("Transcribing your voice command...")
    audio_bytes = voice_input['bytes']
    audio_file = {'audio_file': ('recorded_audio.wav', audio_bytes, 'audio/wav')}
    try:
        response = requests.post(f"{BACKEND_URL}/transcribe-webaudio", files=audio_file)
        if response.status_code == 200:
            transcription = response.json().get("transcription", "")
            if transcription:
                # If transcription is successful, set the query and flag that input is ready
                st.session_state.latest_user_query = transcription
                st.session_state.user_input_ready = True
        else:
            st.error("Transcription failed. Please try again.")
    except Exception as e:
        st.error(f"Could not connect to transcription service: {e}")

# --- Central Processing Block ---
# This block ONLY runs when the 'user_input_ready' flag is True.
# This prevents the "ghost interaction" bug.
if st.session_state.user_input_ready:
    # Get the user's query from the session state
    prompt = st.session_state.latest_user_query
    
    # Add user message to the UI immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Reset the flag to False to prevent this block from running again on the next rerun
    st.session_state.user_input_ready = False

    # Get the AI's response
    with st.chat_message("assistant"):
        with st.spinner("Vaani is thinking..."):
            # Import backend functions here, just in time, to keep UI snappy
            from core.router import vaani_router
            from core.services import text_to_speech, detect_language
            
            session_id = "streamlit_chat_session"
            response_text, agent_used = vaani_router(prompt, session_id)
        
        with st.spinner("Vaani is speaking..."):
            audio_filename = f"response_{len(st.session_state.messages)}.mp3"
            response_lang_code = detect_language(response_text)
            text_to_speech(response_text, audio_filename.split('.')[0], response_lang_code)
            audio_path = os.path.join("assets", audio_filename)
        
        # Display the final text and audio player
        st.markdown(response_text)
        st.audio(audio_path)
    
    # Add the AI's complete response to the message history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "audio_path": audio_path
    })
    
    # Force a rerun of the script. This is crucial for clearing the input widgets
    # and ensuring the app is ready for the next user input.
    st.rerun()

# --- Initial Welcome Message ---
# This special block runs ONLY if the chat history is completely empty.
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("Hello! I'm VaaniVerse. To start, please tell me which language you'd like to talk in. (e.g., English, हिंदी, Español)")
    # We add the welcome message to the history so this block doesn't run again.
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I'm VaaniVerse. To start, please tell me which language you'd like to talk in. (e.g., English, हिंदी, Español)"
    })
    st.rerun()