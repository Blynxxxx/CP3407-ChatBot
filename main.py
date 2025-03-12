import streamlit as st
import requests
import json

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
    languages = ["English", "中文", "မြန်မာ", "Tiếng Việt", "ไทย", "한국어", "日本語"]
    selected_language = st.selectbox(
        "Language Choice:",
        options=languages,
        index=languages.index("English")
    )
    
    if st.session_state.language != selected_language:
        st.session_state.language = selected_language
        st.rerun()

    if st.button("➕ New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()    
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat History
    st.markdown('<div class="history-section">', unsafe_allow_html=True)
    st.markdown('💬 **CHAT HISTORY**')
    st.markdown('</div>', unsafe_allow_html=True)
    
    chat_history_items = [
        "Additional chat history item 1...",
        "Additional chat history item 2...",
        "Additional chat history item 3...",
        "Additional chat history item 4...",
        "Additional chat history item 5...",
        "Additional chat history item 6...",
        "Additional chat history item 7...",
        "Additional chat history item 8...",
        "Additional chat history item 9..."
    ]

    for item in chat_history_items:
        st.sidebar.markdown(f"- {item}")
    
    # Bottom Controls
    st.markdown('<div class="bottom-controls">', unsafe_allow_html=True)
    st.button("💭 Feedback", use_container_width=True)
    st.button("⚙️ Settings", use_container_width=True)
    st.button("❓ Help", use_container_width=True)
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