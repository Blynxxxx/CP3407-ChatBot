from pymongo import MongoClient
import os
from google.generativeai import GenerativeModel

class MongoDB:
    def __init__(self):
        mongo_url = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = MongoClient(mongo_url)
        self.db = self.client["faq_database"]  # Select database
        self.collection = self.db["faq_answers"]  # Selection set

    def find_answer(self, query):
        # Find out if there is already a FAQ Answer
        result = self.collection.create_index([("question", 1)])
        if result:
            return result.get("answer", None)
        return None

    def store_answer(self, question, answer):
       # Storing new AI-generated answers to MongoDB
        self.collection.update_one(
            {"question": question},
            {"$set": {"answer": answer}},  # Updating or inserting answers
            upsert=True  # If there is no such problem, insert a new record
        )

from google.generativeai import GenerativeModel

gemini_api_key = "GEMINI_API_KEY"
model = GenerativeModel("models/embedding-001")

def get_embedding(text):
    return model.embed_content(text)["embedding"] 

# Generate a vector of FAQs
question = "What are the orientation activities?"
embedding = get_embedding(question)
print(embedding)

client = MongoClient("mongodb://localhost:27017")
db = client["orientation_db"]

faq_data = {
    "question": "What are the orientation activities?",
    "answer": "Orientation includes campus tours, academic briefings, and social events.",
    "embedding": get_embedding("What are the orientation activities?")  # 存入生成的向量
}

db.faq_answers.insert_one(faq_data)