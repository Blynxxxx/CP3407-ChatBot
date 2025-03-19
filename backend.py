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
PDF_PATH = 'uploaded_pdfs/TR1S-Full-Time-Orientation-Schedule.pdf'
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

@app.route("/chat", methods=["POST"])
def chat():
    # Handling Chat Enquiry
    data = request.json
    query = data.get("message", "")

    if not query:
        return jsonify({"response": "Error: Empty query!"})

    store_path = os.path.join("vector_stores", "orientation")

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)