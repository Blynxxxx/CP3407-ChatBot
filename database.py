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
        self.feedback_collection = self.db["user_feedback"]
        self.fs = gridfs.GridFS(self.db)
        self.vector_store = self.db["vector_store"]

    def insert_document(self, collection_name, document, question=None, answer=None, source_file=None):
        if question and answer:
            document["question"] = question
            document["answer"] = answer
        self.db[collection_name].insert_one(document)


    def find_answer(self, query):
        if not query.strip():
            return None 
        try:
           result = self.faq_collection.find_one(
               {"$text": {"$search": query}},  # Using Full-Text Indexing
               {"score": {"$meta": "textScore"}}  # Getting the score of a text match
            )
           return result.get("answer", "No answer found.") if result else None
        
        except Exception as e:
            print(f"Database error: {e}")
            return None

    def upload_file(self, file_path):
        file_name = os.path.basename(file_path)

        existing_file = self.db["fs.files"].find_one({"filename": file_name})
        if existing_file:
            print(f"✅ file {file_name} already stored in GridFS, ID: {existing_file['_id']}")
            return existing_file["_id"]
        
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

    def upload_faiss_index(self, faiss_path, pkl_path, language="en"):
    #Upload index.faiss and index.pkl from FAISS to MongoDB GridFS.Save the files with a language prefix such as en_index.faiss / en_index.pkl.
        for path in [faiss_path, pkl_path]:
            if not os.path.exists(path):
                print(f"❌ File does not exist, skip upload：{path}")
                continue

        # Generate filenames with language prefixes, e.g. en_index.faiss
            filename = os.path.basename(path)
            lang_tagged_filename = f"{language}_{filename}"  # 例如 zh_index.pkl

        # Delete the old version (if it exists)
            existing_file = self.db["fs.files"].find_one({"filename": lang_tagged_filename})
            if existing_file:
                self.fs.delete(existing_file["_id"])
                print(f"♻️ Old documents deleted：{lang_tagged_filename}")

        # Upload a new file
            with open(path, "rb") as f:
                file_id = self.fs.put(f, filename=lang_tagged_filename)
                print(f"☁️ New files uploaded：{lang_tagged_filename}，ID: {file_id}")
        


   