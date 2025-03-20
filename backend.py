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

gemini_api_key = os.getenv("GEMINI_API_KEY")
print("Gemini API Key:", gemini_api_key)

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
    
    #     stored_answer = db.find_answer(query)
    #     if stored_answer:
    #         return jsonify({"response": stored_answer})
    # except Exception as e:
    #     print(f"Error querying MongoDB: {e}")
    #     stored_answer = None
    #     return jsonify({"response": "No relevant data found (vector logic is commented out)."})

    # store_path = os.path.join("vector_stores", "orientation")

    # embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
    # vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)

    # docs = vector_store.similarity_search(query=query, k=5)

    #     # Setting the Prompt
    # prompt = (
    #         f"You are a James Cook University  Koalion and you are here to help Q&A regarding orientation information for new students. if no information found to answer, refer "
    #         f"Based on the given information and text, answer the question: '{query}' in detail."
    #         f"Example 1: Question: Where is the Explore Booth?; Response: The Explore Booth is in Block E"
    #         f"Example 2: Question: What is the venue of Network with Lecturers and Peers?; Response: The Network with Lecturers and Peers is in Multi-Purpose Hall"
    #         # f"""Detail orientation timetable information:
    #         # 09:00 AM - 09:05 AM : Welcome Speech by Deputy Vice-Chancellor, Singapore; Welcome Speech by Acting Campus Dean & Head of Learning, Teaching and Student Engagement - Venue: Block C
    #         # 09:05 AM - 09:10 AM : JCU 101 - Venue: Block C
    #         # 09:10 AM to 10:25 AM : DigiLearn Workshop & Academic Advising - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Diploma and Bachelor of Business Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Postgraduate Business and Postgraduate Qualifying; Programs - Business - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Bachelor of Environmental Science Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Diploma and Bachelor of Arts and Psychological Science Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Master of Psychological Science, Graduate Diploma of Psychology and Graduate Certificate of Psychological Science Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Diploma, Bachelor, and Master of Information Technology and Science Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Pre-University Foundation Programs - Venue: Block C
    #         # 10:40 AM - 11:40 AM : Introduction to ELPP - Venue: Block C
    #         # 01:30 PM to 03:00 PM : Explore Booths - Venue: Block E
    #         # 03:00 PM to 05:00 PM : Network with Lecturers and Peers - Venue: Multipurpose Hall
    #         # """
    #         )
                
    # llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)  # Adjust temperature
    # chain = load_qa_chain(llm=llm, chain_type="stuff")

    # if docs:
    #     response = chain.run(input_documents=docs, question=prompt)

    #     # Check if the response indicates a negative result
    #     negative_indicators = [
    #         "not contain information",
    #         "the text only mentions",
    #         "no relevant information",
    #         "unable to answer",
    #         "not found",
    #         "does not provide",
    #         "don't know "
    #     ]

    #     if not response or any(indicator in response.lower() for indicator in negative_indicators):
    #     # If the response is not satisfactory, use Gemini AI for a more general answer
    #         prompt = (
    #                 f"You are a James Cook University Koalion. Answer the following question based on general knowledge: '{query}'. "
    #                 "If you cannot find specific information, provide a helpful response."
    #             )
    #         response = llm.invoke(prompt)
    # else:
    #     response = llm.invoke(prompt)

    # return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)