import streamlit as st
import requests
import json
from dotenv import load_dotenv
from langdetect import detect
from googletrans import Translator
import asyncio
import re

load_dotenv()

# Streamlit UI
st.set_page_config(page_title="Orientation Chatbot", page_icon="JCU.png", layout="wide")

st.markdown("<h1 style='text-align: center;'>JCU Orientation Chatbot 🎈</h1>", unsafe_allow_html=True)

#############################################################################################
# Load translations from languages.json
def load_translations():
    try:
        with open('languages.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        st.error(f"Error loading translations: {str(e)}")
        return {}
    
translations = load_translations()

def get_text(key):
    lang = st.session_state.language
    if lang not in translations or key not in translations[lang]:
        lang = "English"
    return translations[lang].get(key, "Type your message...")

def translate_text(text, source_language, target_language):
    from googletrans import Translator

    # Reserved word substitution (if required)
    preserved_terms = {
        "James Cook": "JAMES_COOK"
    }

    for term, placeholder in preserved_terms.items():
        text = text.replace(term, placeholder)

    translator = Translator()
    try:
        translated = translator.translate(text, src=source_language, dest=target_language)
        result = translated.text
    except Exception as e:
        print(f"[translation error] {e}")
        result = text  # fallback

    # revert to the original wording
    for term, placeholder in preserved_terms.items():
        result = result.replace(placeholder, term)

    return result

#########################################################################

# Function to handle message sending to the backend
def send_message_to_backend(message, user_language, chat_history=None):
    try:
        # If not in English, translate into English first
        if user_language != "en":
            translated_message = translate_text(message, user_language, "en")
        else:
            translated_message = message

        payload = {
            "message": translated_message,
            "language": "English"
        }

        if chat_history:
            payload["chat_history"] = chat_history
        
        response = requests.post("http://127.0.0.1:5000/chat", json=payload)

        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"❌ Server Error: {str(e)}"
    except requests.exceptions.JSONDecodeError:
        return "❌ Server Error: Invalid response format"
    
    english_response = data.get("response", "⚠️ AI could not provide a suitable answer")
    
    return translate_text(english_response, "en", user_language) if user_language != "en" else english_response

def display_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

# User Input Processing
def handle_input(input_content):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Check for empty input
    if not input_content.strip():
        st.warning("Please enter a valid message.")
        return

    # Logging User Messages
    st.session_state.messages.append({"role": "user", "content": input_content})

    # Detecting user language
    try:
        detected_language = detect(input_content) if input_content else "en"
    except Exception:
        detected_language = "en"  # Default to English if detection fails

    # Force detected language to match selected language
    if st.session_state.language == "中文":
        detected_language = "zh-cn"
    elif st.session_state.language == "日本語":
        detected_language = "ja"
    elif st.session_state.language == "한국어":
        detected_language = "ko"
    elif st.session_state.language == "ไทย":
        detected_language = "th"
    elif st.session_state.language == "Tiếng Việt":
        detected_language = "vi"
    elif st.session_state.language == "မြန်မာ":
        detected_language = "my"
    else:  # Default to English if not any of the above
        detected_language = "en"

    # Get the last 10 chats and prevent errors when they are empty.
    chat_history = st.session_state.messages[-10:] if st.session_state.messages else []

    # Use send_message_to_backend(), deliver detected_language.
    chatbot_response = send_message_to_backend(input_content, detected_language, chat_history)

    # Record AI Answer
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
    st.rerun()

# Initialize session state
if "language" not in st.session_state:
    st.session_state.language = "English"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    role = get_text("user") if message["role"] == "user" else get_text("assistant")
    display_message(role, message["content"])

# Quick Questions Section - Positioned above User Input
st.markdown("### Quick Questions")
questions = ["Orientation Schedule?", "Compulsory documents to bring for Student Pass?", "How many type of orientation are there?", "About James Cook University Singapore"]
col1, col2, col3, col4 = st.columns(4)

# Create buttons for each question
for i, question in enumerate(questions):
    with eval(f'col{i % 4 + 1}'):
        if st.button(question):
            handle_input(question)  # Handle quick question input

# User input
if user_input := st.chat_input(get_text("chat_placeholder")):
    handle_input(user_input)  # Handle user input

##########################################################################################

# Sidebar Information
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
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
    
    # Bottom Controls
    st.markdown('<div class="bottom-controls">', unsafe_allow_html=True)

    # Feedback button
    if st.button(f"💭 {get_text('feedback')}", use_container_width=True):
        st.session_state.show_feedback = not st.session_state.get("show_feedback", False)

    # Help button
    if st.button(f"❓ {get_text('help')}",  use_container_width=True):
        st.session_state.show_help = not st.session_state.get("show_help", False)

    # * Show Help content*   
    if st.session_state.get("show_help", False):
        st.markdown('<div class="help-section">', unsafe_allow_html=True)
        st.markdown("""
        *📧 Contact Support:*  
        - Email: [support@example.com](mailto:support@example.com)  
        - FAQ: [Visit FAQ Page](#)
        """, unsafe_allow_html=True)
        if st.button("❌ Close Help", key="close_help", use_container_width=True):
            st.session_state.show_help = False
        st.markdown('</div>', unsafe_allow_html=True)
    
    # * Show Feedback content*
    if st.session_state.get("show_feedback", False):
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        st.markdown("### 💬 Feedback")

        feedback_text = st.text_area("Enter your feedback here...")

        # *Disable button logic*
        submit_button = st.button("Submit Feedback", disabled=not bool(feedback_text.strip()))
        
        if submit_button:
            response = requests.post(
                "http://127.0.0.1:5000/submit_feedback",
                json={"feedback": feedback_text.strip()}
            )
            
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    st.success(f"✅ {res_json.get('message', 'Feedback submitted successfully!')}")
                except requests.exceptions.JSONDecodeError:
                    st.error("❌ Feedback submitted, but received an invalid response.")
            else:
                try:
                    res_json = response.json()
                    st.error(f"❌ Failed to submit feedback: {res_json.get('message', 'Unknown error')}")
                except requests.exceptions.JSONDecodeError:
                    st.error("❌ Failed to submit feedback: Unknown error from server.")
        
        if st.button("❌ Close Feedback", key="close_feedback", use_container_width=True):
            st.session_state.show_feedback = False

        st.markdown('</div>', unsafe_allow_html=True)