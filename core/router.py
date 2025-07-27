import os
import json
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# --- 1. Import all necessary components (with the new JSON function) ---
from core.memory import get_or_create_session, save_user_profile
from core.prompts import (
    ROUTER_TEMPLATE, SYSTEM_PROMPT, WELFARE_AGENT_TEMPLATE,
    TRAVEL_AGENT_TEMPLATE, MENTOR_AGENT_TEMPLATE
)
# --- THE FIX: Import the new, specialized function ---
from core.services import get_llm_response, get_json_response_from_llm, detect_language, translate_text

# Import the modular agent classes from their correct location
from agents.welfare_agent import WelfareAgent
from agents.travel_agent import TravelAgent
from agents.mentor_agent import MentorAgent
from agents.base_agent import welfare_vs, travel_vs, mentor_vs

load_dotenv()

# --- 2. Initialize an instance of each agent ---
print("Initializing agent instances...")
welfare_agent = WelfareAgent(vector_store=welfare_vs, prompt_template=WELFARE_AGENT_TEMPLATE)
travel_agent = TravelAgent(vector_store=travel_vs, prompt_template=TRAVEL_AGENT_TEMPLATE)
mentor_agent = MentorAgent(vector_store=mentor_vs, prompt_template=MENTOR_AGENT_TEMPLATE)
print("Agent instances initialized.")


# --- 3. The Main Router Logic (Augmented with Advanced Features) ---
def vaani_router(query, sid):
    """
    The definitive, intelligent router that handles onboarding, mood detection,
    special commands, and passes a full, persistent user profile to the agents.
    """
    session, user_profile = get_or_create_session(sid)
    memory = session["memory"]
    chat_history = memory.load_memory_variables({}).get('chat_history', [])

    # --- Language Onboarding Logic (Unchanged and correct) ---
    if session.get("is_onboarding"):
        lang_code_prompt = f"What is the two-letter ISO 639-1 code for the language '{query}'? Respond with ONLY the code."
        lang_code = get_llm_response(lang_code_prompt).strip().lower()
        if len(lang_code) != 2: lang_code = detect_language(query)
        
        user_profile["language_preference"] = lang_code
        save_user_profile(sid, user_profile)
        
        session["is_onboarding"] = False
        confirmation_prompt = f"You are Vaani. Your user chose to speak in '{lang_code}'. Respond with a short, warm confirmation in that language."
        response_text = get_llm_response(confirmation_prompt)
        return response_text, "LanguageSetup"

    if user_profile.get("language_preference") is None:
        session["is_onboarding"] = True
        return "Hello! Welcome to VaaniVerse. Which language would you like to talk in?\n(e.g., English, हिंदी, Español)", "LanguageSetup"
        
    # --- Normal Operation ---
    stored_lang_code = user_profile["language_preference"]
    translated_query = translate_text(query, target_language="en")

    # --- Advanced Pre-Analysis Layer ---
    pre_analysis_prompt = f"""
    Analyze the user's query: '{translated_query}'.
    1.  Detect Mood: What is the user's likely mood? (Options: happy, adventurous, stressed, curious, neutral).
    2.  Detect Special Command: Does the query contain a special command? (Options: bookmark, save progress, ask anonymous, none).
    Respond with a valid JSON object with keys "mood" and "command". Example: {{"mood": "adventurous", "command": "bookmark"}}
    """
    try:
        # --- THE FIX: Use the specialized JSON function for this call ---
        analysis_result_str = get_json_response_from_llm(pre_analysis_prompt)
        analysis_result = json.loads(analysis_result_str)
        user_profile["mood"] = analysis_result.get("mood", user_profile.get("mood", "neutral"))
        special_command = analysis_result.get("command", "none")
        print(f"Pre-analysis successful. Mood: {user_profile['mood']}, Command: {special_command}")
    except (json.JSONDecodeError, AttributeError):
        special_command = "none"
        print("Pre-analysis failed to parse JSON, proceeding with standard routing.")

    # --- Handle Special Commands (Unchanged and correct) ---
    if special_command == "bookmark":
        last_response = chat_history[-1].content if chat_history else "your last suggestion"
        user_profile.setdefault("bookmarked_spots", []).append(last_response)
        save_user_profile(sid, user_profile)
        response_text = "I've bookmarked that for you! What else can I help with?"
        memory.save_context({"input": query}, {"output": response_text})
        return response_text, "BookmarkAgent"
    # (Add similar handlers for "save progress" and "ask anonymous" here)

    # --- Standard Routing Logic (Unchanged and correct) ---
    router_llm = ChatGroq(temperature=0, model_name="llama3-8b-8192", groq_api_key=os.getenv("GROQ_API_KEY"))
    router_prompt = ROUTER_TEMPLATE.format(system_prompt=SYSTEM_PROMPT, chat_history=chat_history, query=translated_query)
    domain = router_llm.invoke(router_prompt).content.strip().upper()
    print(f"ROUTED TO DOMAIN: {domain}")
    
    agent_params = {
        "original_query": query, "translated_query": translated_query,
        "chat_history": chat_history, "lang_code": stored_lang_code,
        "user_profile": user_profile
    }
    
    agent_used = "GeneralAgent"
    
    if "WELFARE" in domain:
        agent_used = "WelfareAgent"; response_text = welfare_agent.run(**agent_params)
    elif "TRAVEL" in domain:
        agent_used = "TravelAgent"; response_text = travel_agent.run(**agent_params)
    elif "MENTORSHIP" in domain:
        agent_used = "MentorMatchAgent"; response_text = mentor_agent.run(**agent_params)
    else:
        general_prompt = f"You are Vaani. User said: '{query}'. Provide a brief, conversational response in this language: '{stored_lang_code}'."
        response_text = get_llm_response(general_prompt)

    memory.save_context({"input": query}, {"output": response_text})
    return response_text, agent_used