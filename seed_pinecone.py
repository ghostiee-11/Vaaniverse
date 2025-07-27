import os
import re
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import HuggingFaceEmbeddings # The new import
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader, CSVLoader

print("Starting Final Pinecone Seeding Process (Local Embeddings & Serverless)...")
load_dotenv()

# --- 1. INITIALIZE CONNECTIONS ---
print("Initializing connections...")
pinecone_api_key = os.getenv("PINECONE_API_KEY")
if not pinecone_api_key:
    raise ValueError("PINECONE_API_KEY not found in .env file.")
pinecone = Pinecone(api_key=pinecone_api_key)

# --- 2. INITIALIZE THE FREE, LOCAL EMBEDDING MODEL ---
print("Loading local Sentence-Transformer model (all-MiniLM-L6-v2)...")
# This model runs on your machine, is free, and very capable.
# The first time you run this, it will download the model (a few hundred MB).
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
print("Model loaded successfully.")

# --- 3. DEFINE THE SERVERLESS SPEC ---
# The new Pinecone free tier uses serverless indexes.
serverless_spec = ServerlessSpec(cloud='aws', region='us-east-1')

# --- 4. DEFINE A HELPER FUNCTION FOR INDEX CREATION ---
def create_pinecone_index(index_name, dimension):
    if index_name in pinecone.list_indexes().names():
        print(f"Index '{index_name}' already exists. Clearing for a fresh seed.")
        pinecone.delete_index(index_name)
    
    print(f"Creating new serverless index '{index_name}' with dimension {dimension}...")
    pinecone.create_index(
        name=index_name, 
        dimension=dimension,
        metric='cosine',
        spec=serverless_spec
    )

# The dimension for our local model is 384
LOCAL_MODEL_DIMENSION = 384

# --- 5. SEED ALL INDEXES ---

# --- WELFARE ---
WELFARE_INDEX_NAME = "welfare-rag"
SCHEMES_DIR = "data/welfare_schemes/"
print(f"\nProcessing Multi-PDF Index: '{WELFARE_INDEX_NAME}'")
all_welfare_docs = []
if os.path.isdir(SCHEMES_DIR):
    for filename in os.listdir(SCHEMES_DIR):
        if filename.lower().endswith(".pdf"):
            try:
                loader = PyPDFLoader(os.path.join(SCHEMES_DIR, filename))
                all_welfare_docs.extend(loader.load_and_split())
            except Exception as e:
                print(f"  - WARNING: Could not load {filename}. Skipping. Error: {e}")
    if all_welfare_docs:
        create_pinecone_index(WELFARE_INDEX_NAME, LOCAL_MODEL_DIMENSION)
        print(f"Seeding {len(all_welfare_docs)} welfare document chunks...")
        PineconeVectorStore.from_documents(all_welfare_docs, embeddings, index_name=WELFARE_INDEX_NAME)
        print("Welfare data successfully seeded.")

# --- MENTOR ---
MENTOR_INDEX_NAME = "mentor-rag"
print(f"\nProcessing Index: '{MENTOR_INDEX_NAME}'")
create_pinecone_index(MENTOR_INDEX_NAME, LOCAL_MODEL_DIMENSION)
loader = CSVLoader("data/mentors.csv")
mentor_docs = loader.load()
print(f"Seeding {len(mentor_docs)} mentor documents...")
PineconeVectorStore.from_documents(mentor_docs, embeddings, index_name=MENTOR_INDEX_NAME)
print("Mentor data successfully seeded.")

# --- TRAVEL ---
TRAVEL_INDEX_NAME = "travel-rag"
print(f"\nProcessing Index: '{TRAVEL_INDEX_NAME}'")
all_travel_docs = []
try:
    with open("data/travel_guide.md", "r") as f:
        content = f.read()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    city_sections = re.split(r'\n## City:', content)
    for section in city_sections:
        if section.strip():
            try:
                city_name, city_content = section.strip().split('\n', 1)
                chunks = text_splitter.split_text(city_content)
                for chunk in chunks:
                    all_travel_docs.append(Document(page_content=chunk, metadata={"city": city_name.strip().lower()}))
            except ValueError:
                continue
    if all_travel_docs:
        create_pinecone_index(TRAVEL_INDEX_NAME, LOCAL_MODEL_DIMENSION)
        print(f"Seeding {len(all_travel_docs)} travel document chunks...")
        PineconeVectorStore.from_documents(all_travel_docs, embeddings, index_name=TRAVEL_INDEX_NAME)
        print("Travel data successfully seeded.")
except FileNotFoundError:
    print(f"ERROR: data/travel_guide.md not found.")

print("\n\nDatabase seeding process complete.")