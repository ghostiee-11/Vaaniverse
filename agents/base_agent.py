from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os

# Load environment variables at the top to ensure they are available for all modules.
load_dotenv()

class AgentRunner:
    """A base class for all specialized agents in the VaaniVerse system."""
    def __init__(self, vector_store, prompt_template):
        self.llm = ChatGroq(temperature=0.1, model_name="llama3-8b-8192", groq_api_key=os.getenv("GROQ_API_KEY"))
        self.vector_store = vector_store
        self.prompt_template = prompt_template
        self.web_search_tool = TavilySearchResults(k=2) # Use k=2 to save tokens

    def run(self, **kwargs):
        """This method must be implemented by each subclass."""
        raise NotImplementedError("Each agent must implement its own run method.")

# --- Centralized Vector Store Initialization ---
# This ensures vector stores are created once and reused.
print("Initializing embeddings and vector stores...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
welfare_vs = PineconeVectorStore.from_existing_index('welfare-rag', embeddings)
travel_vs = PineconeVectorStore.from_existing_index('travel-rag', embeddings)
mentor_vs = PineconeVectorStore.from_existing_index('mentor-rag', embeddings)
print("Vector stores initialized.")