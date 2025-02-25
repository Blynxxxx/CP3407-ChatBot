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

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text.replace("\n", " ") + " "
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text.strip()

def main():
    st.title("📚 Orientation Chatbot")
    
    # Upload a PDF file
    pdf_path = 'data/TR1S-Full-Time-Orientation-Schedule.pdf'  # Update file path if needed

    if os.path.exists(pdf_path):
        text = extract_text_from_pdf(pdf_path)

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=300, 
            length_function=len
        )
        chunks = text_splitter.split_text(text=text)
        # st.write(chunks)
        
        # Initialize Gemini embeddings
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
        except Exception as e:
            st.error(f"Error initializing embeddings: {e}")
            return

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
            with st.spinner("Finding information..."):
                docs = vector_store.similarity_search(query=query, k=5)

                # Refined prompt for comprehensive information
                # prompt = (
                #     f"Based on the documents:\n"
                #     f"Analyse event names, times, dates, venues, and required documents"
                #     f"Check how many events are there in total"
                #     f"1. **Required Documents**: List any required documents specifically mentioned for the student pass and medical check-up.\n"
                #     f"2. **Orientation Schedule**: Include key dates, times, venues and events.\n"
                #     f"3. **Venue Information**: Specify the venue for each event.\n"
                #     f"4. **Instructions for International Students**: Highlight any important notes or requirements specific to international students.\n"
                #     f"Answer the question: '{query}' in detail"
                # )

                prompt = (
                    f"You are a JCUS Koalion and you are here to help Q&A regarding orientation information for new students."
                    f"Based on the given information and text, answer the question: '{query}' in detail"
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
                else:
                    response = "No relevant documents found."

                # Display response with background
                st.markdown(f'<div style="background-color:#f4f4f4;padding:10px;border-radius:10px;">{response}</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    main()