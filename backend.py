from datetime import datetime
from flask import Flask, request, jsonify, send_file
import os
from dotenv import load_dotenv
from database import MongoDB

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain

from faq_generation import generate_faq_response


# Loading Environment Variables
load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
print("Claude API Key:", anthropic_api_key)

app = Flask(__name__)
db = MongoDB()

UPLOAD_FOLDER = "uploaded_pdfs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Upload File API
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    file.save(file_path)  # Save locally first----Make sure Flask can access it by storing a copy of it on the server's disk first
    file_id = db.upload_file(file_path)  # Upload to GridFS
    
    return jsonify({"message": "File uploaded successfully", "file_id": str(file_id)})

# List Uploaded Files API
@app.route("/files", methods=["GET"])
def list_files():
    # List all stored files
    files = db.list_files() # Get all file information from MongoDB GridFS
    return jsonify({"files": files}) # Returns a list of files in JSON format

# Download File API
@app.route("/download/<file_id>", methods=["GET"])
def download_file(file_id):
    # Downloading Files from MongoDB GridFS
    file_info = next((file for file in db.list_files() if str(file["id"]) == file_id), None)
    if not file_info:
        return jsonify({"error": "File not found"}), 404
    
    filename = file_info["filename"]  # Get original file name
    save_path = os.path.join(UPLOAD_FOLDER, filename)  # Use filenames to prevent overwriting

    db.download_file(file_id, save_path)
    return send_file(save_path, as_attachment=True)

# Chat API for FAQ Queries
@app.route("/chat", methods=["POST"])
def chat():
    # Handling Chat Enquiry
    data = request.json
    query = data.get("message", "")

    if not query:
        return jsonify({"response": "Error: Empty query!"}), 400
    
    try:
        response = generate_faq_response(query)
        return jsonify({"response": response})
    except Exception as e:
        print(f"❌ Error processing FAQ query: {e}")
        return jsonify({"response": "An error occurred while processing your request."})

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.json
        if not data:
            print("❌ Error: Received empty JSON request")
            return jsonify({"status": "error", "message": "Empty request body"}), 400

        feedback_text = data.get("feedback", "").strip()
        if not feedback_text:
            print("❌ Error: Feedback is empty")
            return jsonify({"status": "error", "message": "Feedback is empty"}), 400

        # Insert to MongoDB
        feedback_doc = {
            "feedback": feedback_text,
            "timestamp": datetime.utcnow()
        }
        db.insert_document("user_feedback", feedback_doc)

        return jsonify({"status": "success", "message": "Feedback saved!"}), 200
    except Exception as e:
        print(f"❌ Error in submit_feedback: {e}")
        return jsonify({"status": "error", "message": f"Internal Server Error: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)