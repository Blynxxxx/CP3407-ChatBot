from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain_community.vectorstores import FAISS
import shutil

# Loading Environment Variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
print("Gemini API Key:", gemini_api_key)

app = Flask(__name__)

# Setting the PDF file path
PDF_PATH = 'data/TR1S-Full-Time-Orientation-Schedule.pdf'
STORE_PATH = "vector_stores/orientation"

# Set the storage path
UPLOAD_FOLDER ="uploaded_pdfs"
VECTOR_STORE_FOLDER ="vector_stores"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_STORE_FOLDER, exist_ok=True)


# Preprocess PDF and store vectors
def process_pdf(pdf_path, store_path):
    if os.path.exists(PDF_PATH):

        pdf_reader = PdfReader(PDF_PATH)
        text = " ".join([page.extract_text().replace("\n", " ") for page in pdf_reader.pages if page.extract_text()])

        # split text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text.strip())

        # Generate Embedding
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)

        # Processing vector storage
        if os.path.exists(STORE_PATH):
            vector_store = FAISS.load_local(STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        else:
            vector_store = FAISS.from_texts(chunks, embedding=embeddings)
            vector_store.save_local(STORE_PATH)

        return vector_store
    return None

vector_store = process_pdf(PDF_PATH, STORE_PATH)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    # Allows users to upload PDFs and create vector stores 
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
    store_path = os.path.join("vector_stores", "orientation")


    file.save(pdf_path)
    vector_store = process_pdf(pdf_path, store_path)
    
    return jsonify({"message": f"PDF {file.filename} uploaded and processed successfully!"})

@app.route("/chat", methods=["POST"])
def chat():
    # Handling Chat Enquiry
    data = request.json
    query = data.get("message", "")
    pdf_name = data.get("pdf_name", "") # Users can choose between different PDF

    if not query:
        return jsonify({"response": "Error: Empty query!"})

    store_path = os.path.join("vector_stores", "orientation")
    
    if not os.path.exists(store_path):
        return jsonify({"response": f"Error: Vector store for {pdf_name} not found!"})

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
    vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)

    docs = vector_store.similarity_search(query=query, k=3)

        # Setting the Prompt
    prompt = (
            f"Based on the documents, answer the question: '{query}' and check for the following information:\n"
            f"1. Required Documents: Provide required documents if specified\n"
            f"2. Orientation Schedule: Key dates and times for orientation activities.\n"
            f"3. Venue Information: Location for the event asked\n"
            f"4. Instructions for International Students: Any important notes or requirements specific to international students.\n"
            f"5. Additional Resources: Mention any support services or resources available to students during orientation.\n"
            f"Please ensure that the information is clear and well-organized."
        )

    llm = GoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.2, api_version="v1")
    chain = load_qa_chain(llm=llm, chain_type="stuff")
    response = chain.run(input_documents=docs, question=prompt)
    return jsonify({"response": response})


@app.route("/list_pdfs", methods=["GET"])
def list_pdfs():
    # Returns a list of processed PDF files
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return jsonify({"pdfs": pdf_files})


@app.route("/delete_pdf", methods=["POST"])
def delete_pdf():
    # Allows deletion of stored PDF and vector databases
    data = request.json
    pdf_name = data.get("pdf_name", "")

    if not pdf_name:
        return jsonify({"error": "No PDF name provided"}), 400

    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_name)
    store_path = os.path.join("vector_stores", "orientation")

    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    if os.path.exists(store_path):
        shutil.rmtree(store_path)

    return jsonify({"message": f"PDF {pdf_name} and its vector store have been deleted."})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


# # test upload PDF
# curl -X POST -F "file=@data/TR1S-Full-Time-Orientation-Schedule.pdf" http://127.0.0.1:5001/upload


# # chat (Q&A API)
# # Select different PDFs for querying
# # Avoid repeated loading, improve query efficiency
# # Adaptable to multiple users asking questions at the same time
# curl -X POST http://127.0.0.1:5001/chat \
#     -H "Content-Type: application/json" \
#     -d '{"message": "What documents do I need?", "pdf_name": "TR1S-Full-Time-Orientation-Schedule.pdf"}'

# # /list_pdfs (view uploaded PDFs)
# # List all processed PDFs
# # Convenient front-end dynamic update file list
# curl -X GET http://127.0.0.1:5001/list_pdfs

# # /delete_pdf (Delete PDF & Vector Storage)
# # Allows deletion of PDFs and corresponding vector databases
# # Saves storage space
# # Manage old data
# curl -X POST http://127.0.0.1:5001/delete_pdf \
#     -H "Content-Type: application/json" \
#     -d '{"pdf_name": "TR1S-Full-Time-Orientation-Schedule.pdf"}'
