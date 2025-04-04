import streamlit as st
import requests
import json
from dotenv import load_dotenv
from langdetect import detect
from googletrans import Translator
import asyncio

load_dotenv()

# Streamlit UI
st.set_page_config(page_title="Orientation Chatbot", page_icon="JCU.png", layout="wide")

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
    return translations[lang].get(key, "Choose languages...")

# Initialize session state
if "language" not in st.session_state:
    st.session_state.language = "English"
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(f"<h1 style='text-align: center;'>{get_text('app_title')}</h1>", unsafe_allow_html=True)

def translate_text(text, source_language, target_language):
    # Preserve specific terms
    preserved_terms = {
        "James Cook": "JAMES_COOK"
    }
    
    # Replace terms with placeholders
    for term, placeholder in preserved_terms.items():
        text = text.replace(term, placeholder)

    translator = Translator()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    translated = loop.run_until_complete(translator.translate(text, src=source_language, dest=target_language))
    
    # Restore preserved terms
    for term, placeholder in preserved_terms.items():
        translated.text = translated.text.replace(placeholder, term)

    return translated.text

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
            "language": user_language
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

    # # Force detected language to match selected language
    if st.session_state.language == "中文":
        detected_language = "zh-cn"
    else:  # Default to English if not any of the above
        detected_language = "en"

    # Get the last 10 chats and prevent errors when they are empty.
    chat_history = st.session_state.messages[-10:] if st.session_state.messages else []

    # Use send_message_to_backend(), deliver detected_language.
    chatbot_response = send_message_to_backend(input_content, detected_language, chat_history)

    # Record AI Answer
    st.session_state.messages.append({"role": "assistant", "content": chatbot_response})
    st.rerun()

# Display conversation history
for message in st.session_state.messages:
    role = get_text("user") if message["role"] == "user" else get_text("assistant")
    display_message(role, message["content"])

quick_faqs = {
    "en": {
        "When is the orientation for full time and part time?":
            "Orientation for **Full-Time** and **Part-Time** students is held from **Monday, 06 January to Friday, 17 January 2025**. Full-time programs include Business, IT, Science, and more. Part-time students attend sessions relevant to their programs during the same period.",

        "Compulsory documents for Student Pass Formalities?":
            "The required documents include:\n- Passport\n- IPA Letter\n- Academic Certificates and Transcripts\n- Proof of English Proficiency (e.g., IELTS)\n- Signed Advisory Note, Letter of Offer, Student Contract\n- NRIC/Passport and ICA Card\n- Additional documents if applicable",

        "What do I need to prepare for orientation?":
            "Before orientation, complete Student Pass formalities, activate your JCU Email and Student ID, set up your LearnJCU account, and prepare any required documents for verification. You should also check the JCU Calendar and bring your own device (laptop recommended).",

        "About James Cook University Singapore":
            "James Cook University Singapore (JCUS) is a branch campus of James Cook University Australia. Located in Sims Drive, Singapore, it offers programs in Business, IT, Psychology, Science, Education, and more. JCUS promotes student development through academic excellence and support services."
    },
    "zh": {
        "When is the orientation for full time and part time?":
            "迎新会时间为：**2025年1月6日（星期一）至1月17日（星期五）**，适用于全日制与非全日制学生。\n全日制课程包括：商科、IT、理科等。\n非全日制学生将在同一期间参加相关活动。",

        "Compulsory documents for Student Pass Formalities?":
            "您需要准备的文件包括：\n- 护照\n- IPA信\n- 学术证书与成绩单\n- 英语水平证明（如IELTS）\n- 咨询说明书、录取通知书与学生合同\n- 身份证或护照及ICA登机卡\n- 如适用，其他补充材料",

        "What do I need to prepare for orientation?":
            "在迎新前，您需要完成学生准证手续、激活JCU邮箱和学号，注册LearnJCU账户，并准备好核查所需文件。\n建议携带笔记本电脑并查看JCU日历了解重要时间节点。",

        "About James Cook University Singapore":
            "詹姆斯库克大学新加坡校区（JCUS）是詹姆斯库克大学澳大利亚的海外分校，位于新加坡Sims Drive，提供商科、IT、心理学、理科、教育等课程，并致力于通过高质量教学和全面学生支持服务促进学生发展。"
    }
}

# Render quick buttons with fixed answers
st.markdown(f"### {get_text('quick_questions')}")
lang_code = "zh" if st.session_state.language == "中文" else "en"

col1, col2, col3, col4 = st.columns(4)
buttons = list(quick_faqs[lang_code].keys())
cols = [col1, col2, col3, col4]

for i, question in enumerate(buttons):
    display_text = get_text(question)  # Show translated Chinese buttons
    with cols[i % 4]:
        if st.button(display_text):
            answer = quick_faqs[lang_code][question]  # The answer is still in English.
            st.session_state.messages.append({"role": "user", "content": display_text})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

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