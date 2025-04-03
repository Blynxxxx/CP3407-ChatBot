import os
from dotenv import load_dotenv
from flask import app, jsonify, request
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from PyPDF2 import PdfReader
from docx import Document
from pymongo import MongoClient
import gridfs
from database import MongoDB

# Loading Environment Variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Connecting to MongoDB
client = MongoClient("mongodb+srv://AICHATBOT:2025aichatbot@db.mfbl1.mongodb.net/")
db = client["orientation_db"]
fs = gridfs.GridFS(db)

# Setting the storage path
UPLOAD_FOLDER = "uploaded_pdfs"
VECTOR_STORE_FOLDER = "vector_stores"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_STORE_FOLDER, exist_ok=True)


# Setting the vector storage path
store_path = os.path.join(VECTOR_STORE_FOLDER, "orientation")

# Generate Embed
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)

# Initialize Claude model
llm = ChatAnthropic(model='claude-3-sonnet-20240229', api_key=anthropic_api_key, temperature=0.2, max_tokens=1024)

def extract_text_from_pdf(pdf_path):
   # Extract text from PDF file
    reader = PdfReader(pdf_path)
    text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text.strip()

def extract_text_from_docx(docx_path):
    # Extract text from Word documents (.docx)
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text

# Uploading Files to MongoDB GridFS
def upload_file_to_mongodb(file_path, use_gridfs=True):
    filename = os.path.basename(file_path)
    file_id = None

    if use_gridfs:
        with open(file_path, "rb") as file:
            file_id = fs.put(file, filename=filename)  # Access GridFS
            db["files"].update_one({"filename": filename}, {"$set": {"gridfs_id": file_id}}, upsert=True)  # Record GridFS ID
            print(f"file {filename} already stored in GridFS，ID: {file_id}")
    else:
        db["files"].update_one({"filename": filename}, {"$set": {"file_type": filename.split('.')[-1], "uploaded_at": os.path.getmtime(file_path)}}, upsert=True)
        print(f"✅ file {filename} stored in General MongoDB（haven't use GridFS）")

    return file_id

# Downloading files from GridFS
def download_file(file_id, save_path):
    file_doc = db["files"].find_one({"_id": file_id})
    if not file_doc:
        print(f"❌ file {file_id} do not exist in `files`")
        return

    filename = file_doc["filename"]
    local_file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Read the first 10 bytes to check for file corruption
    if os.path.exists(local_file_path):
        try:
            with open(local_file_path, "rb") as f:
                f.read(10)
            print(f"Locally Existing {filename}")
            return
        except Exception:
            print(f" {filename} Corrupted, re-download...")

    # Re-download from `GridFS`
    if "gridfs_id" in file_doc:
        gridfs_id = file_doc["gridfs_id"]
        with open(save_path, "wb") as file:
            file.write(fs.get(gridfs_id).read())
        print(f"{filename} Successful re-download from GridFS")
    else:
        print(f"{filename} Neither locally nor in GridFS!")


def process_files():
    # Processes uploaded PDF and Word documents, converting text to vectors and depositing them into FAISS
    file_docs = db["files"].find()
    # Get the list of uploaded files
    uploaded_files = list(file_docs)
    print(f"📂 Found {len(uploaded_files)} uploaded files in MongoDB.")

    all_text = ""
    
    for file in uploaded_files:
        file_id = file["_id"]

        if "filename" not in file:
            print(f"❌ Error: Missing 'filename' in file document: {file}")
            continue  # Skip this file to avoid KeyError!
        
        filename = file["filename"]
        print(f"✅ Processing file: {filename}")

        local_path = os.path.join(UPLOAD_FOLDER, filename)

        # Download file
        download_file(file_id, local_path)

        # Parsing PDF files
        if filename.lower().endswith(".pdf"):
            file_text = extract_text_from_pdf(local_path)
        # Parsing Word documents
        elif filename.lower().endswith(".docx"):
            file_text = extract_text_from_docx(local_path)
        else:
            continue  # Ignore files in other formats

        all_text += f"\n---\n{file_text}"

    if not all_text.strip():
        print("No extractable text found.")
        return

    # split text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(all_text.strip())

    # Load or create a FAISS vector database
    if os.path.exists(store_path):
        vector_store = get_faiss_store()
        print("🔄 Existing FAISS vector store loaded. Updating with new data...")
        vector_store.add_texts(chunks)  # **Automatic addition of new data**
    else:
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
        print("🆕 Creating a new FAISS vector store.")

    # Keep an up-to-date FAISS database
    vector_store.save_local(store_path)()
    print("✅ FAISS vector store updated successfully!")

def generate_prompt(query, language="en"):
    if language == "zh":
        return f"""
您是一名新生的迎新助理。您需要回答关于詹姆斯库克大学新加坡的迎新信息。请用自然语言回答问题，不要使用代码格式（例如 print()）
您的目标是根据迎新文件提供结构清晰的答案。
回答时，请使用以下格式：
要点（•）用于一般说明。
确保回答：简洁但详细；语气友好；格式一致，以匹配迎新文件。
寻找名词关键字并注意问题。
根据文件，详细回答问题：'{query}'。
示例 1:问题:探索展位在哪里?; 回答: 探索展位在E栋。
示例 2:问题:与老师和同学的网络活动的地点是什么?; 回答:与老师和同学的网络活动在多功能大厅。
示例 3:詹姆斯库克大学新加坡有多少个楼栋?; 回答: 詹姆斯库克大学新加坡有5个楼栋。A栋, B栋, C栋, D栋和E栋。
"""
    else:  # Default to English
        return f"""
You are an Orientation Assistant for new students. You are required to answer orientation information about James Cook University Singapore.
Your goal is to provide structured and clear answers based on orientation documents.Do **not** use code formatting like `print()` or `console.log()`, just give a helpful answer.
When responding, organize the answer using:
Numbered points (1., 2., 3.) for multiple details.
Bullet points (•) for general explanations.
Ensure responses are: Concise but detailed; Friendly and supportive; Formatted consistently to match orientation documents.
Search for noun key words and pay attention to questions.
Based on the documents, answer the question: '{query}' in detail.
Example 1: Question: Where is the Explore Booth?; Response: The Explore Booth is in Block E.
Example 2: Question: What is the venue of Network with Lecturers and Peers?; Response: The Network with Lecturers and Peers is in Multi-Purpose Hall.
Example 3: How many blocks/buildings in JCU Singapore?; Response: There are 5 blocks in JCU Singapore: Block A, B, C, D, and E.
"""

faiss_cache = None  # Defining the Global Cache

def get_faiss_store(): # Use global cache to avoid double loading FAISS
    global faiss_cache
    if faiss_cache is None:  # Load only on first enquiry
        faiss_cache = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
    return faiss_cache

def generate_faq_response(query, chat_history=None):

    # First query the database to see if there is an answer already stored.
    mongo = MongoDB()

    # Query Database
    stored_answer = mongo.find_answer(query)
    if stored_answer:
        return stored_answer
    try:
        vector_store = get_faiss_store()
        docs = vector_store.similarity_search(query=query, k=5)
    except Exception as e:
        print(f"❌ Error loading FAISS vector store: {e}")
        docs = []

        history_context = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]) if chat_history else ""

    # Generate Prompt
    prompt = generate_prompt(query)

    # Initialising the LLM
    llm = GoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
    chain = load_qa_chain(llm=llm, chain_type="stuff")


    if docs:
        response = chain.run(input_documents=docs, question=prompt)

        # Filtering useless AI answers
        negative_indicators = [
            "not contain information",
            "the text only mentions",
            "no relevant information",
            "unable to answer",
            "not found",
            "does not provide",
            "don't know",
            "do not contain",
            "sorry",
            "do not have",
            "do not provide"
        ]

        if not response or any(indicator in response.lower() for indicator in negative_indicators):
            # Using AI to Generate General Answers
            general_prompt = f"""
            You are an JCU(James Cook University) AI assistant answering student questions using internet to provide a helpful response.
            
            Question: '{query}'
            """
            response = llm.invoke(general_prompt)
    else:
        response = llm.invoke(prompt)
    return response

if __name__ == "__main__":
    process_files()
