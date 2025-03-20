from pymongo import MongoClient
import gridfs
import os
from dotenv import load_dotenv
import base64
import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI is not set. Please check your .env file.")

DB_NAME = "orientation_db"

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.faq_collection = self.db["faq"]
        self.fs = gridfs.GridFS(self.db)
        self.vector_store = self.db["vector_store"]

    def insert_document(self, question, answer, source_file=None):
        document = {"question": question, "answer": answer}
        if source_file:
            document["source_file"] = source_file
        self.faq_collection.insert_one(document)

    def find_answer(self, query):
        if not query.strip():
            return None 
        try:
            result = self.faq_collection.find_one({"question": {"$regex": query, "$options": "i"}})
            return result.get("answer", "No answer found.") if result else None
        except Exception as e:
            print(f"Database error: {e}")
            return None

    def upload_file(self, file_path):
        file_name = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()
            file_id = self.fs.put(file_data, filename=file_name)
        return file_id

    def download_file(self, file_id, save_path):
        file_data = self.fs.get(file_id)
        with open(save_path, "wb") as f:
            f.write(file_data.read())

    def list_files(self):
        return [{"filename": file.filename, "id": str(file._id)} for file in self.fs.find()]

    def close_connection(self):
        self.client.close()

    def upload_faiss_index(self, faiss_path="vector_stores/orientation/index.faiss", 
                            pkl_path="vector_stores/orientation/index.pkl"):

       return

   