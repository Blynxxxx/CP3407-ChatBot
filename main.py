import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Streamlit UI
st.set_page_config(page_title="Orientation Chatbot", page_icon="JCU.png", layout="wide")

st.markdown("<h1 style='text-align: center;'>JCU Orientation Chatbot 🎈</h1>", unsafe_allow_html=True)

# # Load custom CSS
# with open('style.css') as f:
#     st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load translations from languages.json
def load_translations():
    try:
        with open('languages.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading translations: {str(e)}")
        return {}
    
# Function to handle message sending to the backend
def send_message_to_backend(message):
    try:
        response = requests.post(
            "http://127.0.0.1:5000/chat",
            json={
                "message": message,
                "language": st.session_state.language
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", get_text("no_results"))
    except requests.exceptions.RequestException as e:
        return f"{get_text('error')} {str(e)}"
    except requests.exceptions.JSONDecodeError:
        return f"{get_text('error')} Received non-JSON response"

# Function to display messages
def display_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

# Function to handle user and quick question inputs
def handle_input(input_content):
    st.session_state.messages.append({"role": "user", "content": input_content})
    chatbot_response = send_message_to_backend(input_content)
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
    st.rerun()

# Initialize session state
if "language" not in st.session_state:
    st.session_state.language = "English"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load translations
translations = load_translations()

# Get current language text
def get_text(key):
    lang = st.session_state.language
    if lang not in translations or key not in translations[lang]:
        lang = "English"
    return translations[lang].get(key, f"Missing translation: {key}")

# Function to handle message sending to the backend
def send_message_to_backend(message):
    try:
        response = requests.post(
            "http://127.0.0.1:5000/chat",
            json={
                "message": message,
                "language": st.session_state.language
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", get_text("no_results"))
    except requests.exceptions.RequestException as e:
        return f"{get_text('error')} {str(e)}"
    except requests.exceptions.JSONDecodeError:
        return f"{get_text('error')} Received non-JSON response"

# Function to display messages
def display_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

# Sidebar Information
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Language Selection
    # st.markdown(f"<b>{get_text('language')}</b>", unsafe_allow_html=True)
    # st.markdown('<div class="language-section">', unsafe_allow_html=True)
    # languages = ["English", "中文", "မြန်မာ", "Tiếng Việt", "ไทย", "한국어", "日本語"]
    languages = list(translations.keys())
    selected_language = st.selectbox(
        get_text("language"),
        options=languages,
        index=languages.index(st.session_state.language)
    )
    
    if st.session_state.language != selected_language:
        st.session_state.language = selected_language
        st.rerun()

    if st.button(f"➕ {get_text('new_chat')}", use_container_width=True):
        # Empty chat records after clicking
        st.session_state.messages = []
        st.rerun()    
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat History
    st.markdown('<div class="history-section">', unsafe_allow_html=True)
    # st.markdown('💬 **CHAT HISTORY**')
    st.markdown(f"💬 **{get_text('chat_history')}**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Controls
    st.markdown('<div class="bottom-controls">', unsafe_allow_html=True)
    # st.button("💭 Feedback", use_container_width=True)
    # st.button("⚙️ Settings", use_container_width=True)
    # st.button("❓ Help", use_container_width=True)
    st.button(f"💭 {get_text('feedback')}", use_container_width=True)
    st.button(f"⚙️ {get_text('settings')}", use_container_width=True)
    st.button(f"❓ {get_text('help')}", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Display conversation history
for message in st.session_state.messages:
    role = get_text("user") if message["role"] == "user" else get_text("assistant")
    display_message(role, message["content"])

# Quick Questions Section - Positioned above User Input
st.markdown("### Quick Questions")
questions = ["Orientation Time?", "What to bring?", "Location of the event?", "Contact information?"]
col1, col2, col3, col4 = st.columns(4)

# Create buttons for each question
for i, question in enumerate(questions):
    with eval(f'col{i % 4 + 1}'):
        if st.button(question):
            handle_input(question)  # Handle quick question input

# User input
if user_input := st.chat_input(get_text("chat_placeholder")):
    handle_input(user_input)  # Handle user input

# for message in st.session_state.messages:
#     role = get_text("user") if message["role"] == "user" else get_text("assistant")
#     # role = " user " if message["role"] == "user" else "assistant"
#     with st.chat_message(role):
#         st.markdown(message["content"])

# # User input
# if user_input := st.chat_input(get_text("chat_placeholder")):
    
#     st.session_state.messages.append({"role": "user", "content": user_input})
    
#     with st.chat_message(get_text("2user")):
#         st.markdown(user_input)

#     try:
#         response = requests.post(
#             "http://127.0.0.1:5000/chat",
#             json={
#                 "message": user_input,
#                 "language": st.session_state.language
#             }
#         )
#         response.raise_for_status()
#         data = response.json()
#         chatbot_response = data.get("response", get_text("no_results"))
#     except requests.exceptions.RequestException as e:
#         chatbot_response = f"{get_text('error')} {str(e)}"
#     except requests.exceptions.JSONDecodeError:
#         chatbot_response = f"{get_text('error')} Received non-JSON response"

#     st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
#     with st.chat_message(get_text("assistant")):
#         st.markdown(chatbot_response)