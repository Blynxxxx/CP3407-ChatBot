import streamlit as st
import requests
import json

# Streamlit UI
st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="wide")

st.title("📚 Orientation Chatbot")

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

# Sidebar Information
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Language Selection
    st.markdown('<div class="language-section">', unsafe_allow_html=True)
    st.title(get_text("title"))
    languages = ["English", "中文", "မြန်မာ", "Tiếng Việt", "ไทย", "한국어", "日本語"]
    selected_language = st.selectbox(
        "Language Choice:",
        options=languages,
        index=languages.index("English")
    )
    
    if st.session_state.language != selected_language:
        st.session_state.language = selected_language
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat History
    st.markdown('<div class="history-section">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('chat_history')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom Controls
    st.markdown('<div class="bottom-controls">', unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button(get_text("feedback"))
        with col2:
            st.button(get_text("settings"))
        with col3:
            st.button(get_text("help"))
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# # Connecting to the back-end API
# BACKEND_URL = "http://127.0.0.1:5000/chat"

# # Chat logs are stored in session_state
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Show history messages
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # user input
# if user_input := st.chat_input("💬 Ask a question about Orientation:"):
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.markdown(user_input)

#     # Send request to backend
#     response = requests.post(BACKEND_URL, json={"message": user_input}).json()["response"]
#     st.session_state.messages.append({"role": "assistant", "content": response})

#     with st.chat_message("assistant"):
#         st.markdown(response)

# User input
if user_input := st.chat_input(get_text("chat_placeholder")):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message(get_text("user")):
        st.markdown(user_input)

    try:
        response = requests.post(
            "http://127.0.0.1:5000/chat",
            json={
                "message": user_input,
                "language": st.session_state.language
            }
        )
        response.raise_for_status()
        data = response.json()
        chatbot_response = data.get("response", get_text("no_results"))
    except requests.exceptions.RequestException as e:
        chatbot_response = f"{get_text('error')} {str(e)}"
    except requests.exceptions.JSONDecodeError:
        chatbot_response = f"{get_text('error')} Received non-JSON response"

    st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
    with st.chat_message(get_text("assistant")):
        st.markdown(chatbot_response)