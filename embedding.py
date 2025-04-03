import os
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient

# 1. Deploying API Keys
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Generate Embedding
text = "This is a chatbot that helps answer questions."
response = genai.embed_content(
    model="models/embedding-001",
    content=text,
    task_type="retrieval_document"
)

embedding = response["embedding"]

# 3. Store in MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["orientation_db"]
collection = db["files"]

# Upsert (update or insert)
collection.update_one(
    {"_id": "vector_search"},
    {"$set": {
        "content": text,
        "embedding": embedding
    }},
    upsert=True
)

print("✅ Embedding saved to MongoDB successfully.")
