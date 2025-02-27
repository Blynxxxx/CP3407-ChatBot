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
            vector_stores = FAISS.load_local(STORE_PATH, embeddings, allow_dangerous_deserialization=True)
        else:
            vector_stores = FAISS.from_texts(chunks, embedding=embeddings)
            vector_stores.save_local(STORE_PATH)

        return vector_stores
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

    docs = vector_store.similarity_search(query=query, k=5)

        # Setting the Prompt
    prompt = (
            f"You are a James Cook University  Koalion and you are here to help Q&A regarding orientation information for new students. if no information found to answer, refer "
            f"Based on the given information and text, answer the question: '{query}' in detail."
            f"Example 1: Question: Where is the Explore Booth?; Response: The Explore Booth is in Block E"
            f"Example 2: Question: What is the venue of Network with Lecturers and Peers?; Response: The Network with Lecturers and Peers is in Multi-Purpose Hall"
            f"""Detail orientation timetable information:
            09:00 AM - 09:05 AM : Welcome Speech by Deputy Vice-Chancellor, Singapore; Welcome Speech by Acting Campus Dean & Head of Learning, Teaching and Student Engagement - Venue: Block C
            09:05 AM - 09:10 AM : JCU 101 - Venue: Block C
            09:10 AM to 10:25 AM : DigiLearn Workshop & Academic Advising - Venue: Block C
            10:40 AM - 11:40 AM : Diploma and Bachelor of Business Programs - Venue: Block C
            10:40 AM - 11:40 AM : Postgraduate Business and Postgraduate Qualifying; Programs - Business - Venue: Block C
            10:40 AM - 11:40 AM : Bachelor of Environmental Science Programs - Venue: Block C
            10:40 AM - 11:40 AM : Diploma and Bachelor of Arts and Psychological Science Programs - Venue: Block C
            10:40 AM - 11:40 AM : Master of Psychological Science, Graduate Diploma of Psychology and Graduate Certificate of Psychological Science Programs - Venue: Block C
            10:40 AM - 11:40 AM : Diploma, Bachelor, and Master of Information Technology and Science Programs - Venue: Block C
            10:40 AM - 11:40 AM : Pre-University Foundation Programs - Venue: Block C
            10:40 AM - 11:40 AM : Introduction to ELPP - Venue: Block C
            01:30 PM to 03:00 PM : Explore Booths - Venue: Block E
            03:00 PM to 05:00 PM : Network with Lecturers and Peers - Venue: Multipurpose Hall
            """
                    )
                
    llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)  # Adjust temperature
    chain = load_qa_chain(llm=llm, chain_type="stuff")

    if docs:
        response = chain.run(input_documents=docs, question=prompt)

        # Check if the response indicates a negative result
        negative_indicators = [
            "not contain information",
            "the text only mentions",
            "no relevant information",
            "unable to answer",
            "not found",
            "does not provide",
            "don't know "
        ]


        if not response or any(indicator in response.lower() for indicator in negative_indicators):
        # If the response is not satisfactory, use Gemini AI for a more general answer
            prompt = (
                    f"You are a James Cook University Koalion. Answer the following question based on general knowledge: '{query}'. "
                    "If you cannot find specific information, provide a helpful response."
                )
            response = llm.invoke(prompt)
    else:
        response = llm.invoke(prompt)

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
