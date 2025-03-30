import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Deploying API Keys
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. generating vectors
response = genai.embed_content(
    model="models/embedding-001",  # Using Google's Embedding Model
    content="This is a chatbot that helps answer questions.",
    task_type="retrieval_document"
)

# 3. Get Embedding Vector
embedding = response["embedding"]
print(embedding)  # Make sure the output is correct
