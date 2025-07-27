import json
import os
from langchain.memory import ConversationBufferWindowMemory

# --- SIMULATED LONG-TERM MEMORY DATABASE ---
# In a real app, this would be a real database (PostgreSQL, MongoDB, etc.)
# For the hackathon, a simple JSON file is a perfect way to demonstrate the concept.
USER_PROFILES_DB = "user_profiles.json"

def load_user_profiles():
    if os.path.exists(USER_PROFILES_DB):
        with open(USER_PROFILES_DB, 'r') as f:
            return json.load(f)
    return {}

def save_user_profiles(profiles):
    with open(USER_PROFILES_DB, 'w') as f:
        json.dump(profiles, f, indent=2)

# Load all profiles into memory when the app starts
USER_PROFILES = load_user_profiles()
SESSION_MEMORY = {}

def get_or_create_session(sid):
    """
    Retrieves or creates a session, now fully integrated with a persistent user profile.
    """
    if sid not in SESSION_MEMORY:
        # Check if this user has a long-term profile
        if sid not in USER_PROFILES:
            print(f"Creating new long-term profile for SID: {sid}")
            USER_PROFILES[sid] = {
                "language_preference": None,
                "name": "User",
                "mood": "neutral",
                "location": "unknown",
                "bookmarked_spots": [],
                "welfare_progress": {},
                "mentor_interactions": 0
            }
        
        print(f"Creating new session for SID: {sid}")
        SESSION_MEMORY[sid] = {
            "memory": ConversationBufferWindowMemory(memory_key="chat_history", k=4, return_messages=True),
            "is_onboarding": USER_PROFILES[sid].get("language_preference") is None
        }
    
    # Always return the combined session and user profile data
    return SESSION_MEMORY[sid], USER_PROFILES[sid]

def save_user_profile(sid, profile_data):
    """Saves the updated user profile to our JSON database."""
    if sid in USER_PROFILES:
        USER_PROFILES[sid].update(profile_data)
        save_user_profiles(USER_PROFILES)
        print(f"Saved updated profile for SID: {sid}")