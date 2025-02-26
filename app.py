import streamlit as st
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
from streamlit_extras.add_vertical_space import add_vertical_space
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, GoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY") 

# Sidebar contents
with st.sidebar:
    st.title('Orientation Chatbot')
    st.markdown('''
    ## About
    This app is an LLM-powered chatbot built using:
    - [StreamLit](https://streamlit.io/)
    - [LangChain](https://python.langchain.com/)
    - [Google Gemini](https://ai.google.dev/)
    ''')
    add_vertical_space(5)
    st.write('Created by Group-8')

def main():
    st.title("📚 Orientation Chatbot")
    
    # Upload a PDF file
    pdf_path = 'data/TR1S-Full-Time-Orientation-Schedule.pdf'  # Update file path if needed

    if os.path.exists(pdf_path):
        pdf_reader = PdfReader(pdf_path)

        # Extract text from PDF
        text = ""
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text.replace("\n", " ") + " "

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200, 
            length_function=len
        )
        chunks = text_splitter.split_text(text=text.strip())  # Strip any leading/trailing whitespace
        
        # Initialize Gemini embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)

        # Create vector store
        store_name = os.path.basename(pdf_path).replace('.pdf', '')
        store_path = f"vector_stores/{store_name}"

        if os.path.exists(store_path):
            vector_store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
        else:
            vector_store = FAISS.from_texts(chunks, embedding=embeddings)
            vector_store.save_local(store_path)

        # Accept user questions/query
        query = st.text_input("💬 Ask a question about Orientation:")

        if query:
            docs = vector_store.similarity_search(query=query, k=3)

            # Improved prompting
            prompt = f"Based on the following documents, answer the question: '{query}'. " \
                     "Please provide a concise and accurate response."
            
            # Enhanced prompt
            # prompt = (
            #     "Based on the following documents, can you tell me what documents I need to bring for my student pass and medical check? "
            #     "The required documents are specifically mentioned."
            # )

            # Refined prompt for comprehensive information
            # prompt = (
            #     f"Based on the documents, answer the question: '{query}' and check for the follow information:\n"
            #     f"1. Required Documents: Provide require documents if specified\n"
            #     f"2. Orientation Schedule: Key dates and times for orientation activities.\n"
            #     f"3. Venue Information: Location for the event asked\n"
            #     f"4. Instructions for International Students: Any important notes or requirements specific to international students.\n"
            #     f"5. Additional Resources: Mention any support services or resources available to students during orientation.\n"
            #     f"Please ensure that the information is clear and well-organized."
            # )
            
            llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.2)  # Adjust temperature
            chain = load_qa_chain(llm=llm, chain_type="stuff")

            if docs:
                response = chain.run(input_documents=docs, question=prompt)
            # else:
            #     response = llm.invoke(prompt)

            # Display response with background
            st.markdown(f'<div style="background-color:#f4f4f4;padding:10px;border-radius:10px;">{response}</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()