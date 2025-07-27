import streamlit as st
import os
import time

st.set_page_config(page_title="VaaniVerse Mission Control", layout="wide")

# --- Header Section ---
if os.path.exists("assets/logo.png"):
    st.image("assets/logo.png", width=100)
st.title("VaaniVerse: The Inclusive Multimodal AI Companion")
st.markdown("### Presented by Team FastAPI | Final Hackathon Demo")
st.markdown("---")

# --- Main Layout: Two Columns ---
col1, col2 = st.columns([3, 2])

with col1:
    st.header("Unified Agentic Ecosystem: Live Monitor")
    log_placeholder = st.empty()

    # This function reads the log file created by api.py to show real-time updates
    def stream_log():
        if os.path.exists("mission_control_log.txt"):
            with open("mission_control_log.txt", "r") as f:
                log_content = f.read()
            log_placeholder.code(log_content, language="bash")
        else:
            log_placeholder.info("System Initialized. Waiting for the first voice call...")

with col2:
    st.header("System Architecture")
    st.success("✅ All Systems Operational")

    with st.container(border=True):
        st.subheader("🧠 VaaniRouter")
        st.write("Classifies queries and routes to the correct specialized agent.")
        st.progress(100, text="Online")

    st.write("Specialized Agents:")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.write("✈️ **Travel**")
            st.caption("RAG + Web Search")
    with c2:
        with st.container(border=True):
            st.write("📚 **Welfare**")
            st.caption("RAG + Web Search")
    with c3:
        with st.container(border=True):
            st.write("🤝 **Mentor**")
            st.caption("RAG Lookup")

    st.markdown("---")
    st.subheader("Core Tech Stack")
    st.write("🚀 **Inference:** Groq LPU (Llama3)")
    st.write("🧠 **Embeddings:** Hugging Face (Local & Free)")
    st.write("💾 **Knowledge Base:** Pinecone Serverless DB")
    st.write("🔍 **Live Search:** Tavily API")
    st.write("🗣️ **Voice I/O:** Twilio API")

# --- Simulated Advanced Features Panel ---
st.markdown("---")
st.header("Inclusive & Multimodal Capabilities")
with st.expander("Click to showcase full platform vision from slides"):
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.subheader("Form Filler Agent")
        if st.button("Simulate Document Upload"):
            st.info("`[OCR Agent]`: Parsing document...")
            st.success("`[FormFiller]`: Application pre-filled!")
    with f_col2:
        st.subheader("ASL-to-Text")
        if st.button("Simulate Sign Language"):
            st.info("`[Vision Agent]`: Reading gesture...")
            st.success("`[Router]`: Understood sign!")
    with f_col3:
        st.subheader("Story Agent")
        if st.button("Generate Mood-based Story"):
            st.info("`[Story Agent]`: Crafting narrative...")
            st.success("`[TTS]`: Story ready to play!")

# --- Auto-refresh Loop to update the log ---
while True:
    stream_log()
    time.sleep(2) # Refresh every 2 seconds