import streamlit as st
import requests
import time

# --- Configuration ---
API_URL = "http://localhost:8000" # Ensure this matches your FastAPI port

st.set_page_config(
    page_title="AI Search Assistant",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for a beautiful UI ---
st.markdown("""
    <style>
    .st-emotion-cache-1c7y2kd {
        flex-direction: row-reverse;
        text-align: right;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- API Helper Functions ---
def register_user(username, password):
    try:
        response = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("🎉 Registration successful! You can now log in.")
        elif response.status_code == 400:
            st.error("⚠️️ Username already exists.")
        else:
            st.error(f"❌ Error: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Could not connect to the backend server. Is FastAPI running?")

def send_chat_message(username, message):
    try:
        response = requests.post(f"{API_URL}/{username}/chat", json={"message": message})
        if response.status_code == 200:
            return response.json().get("response")
        elif response.status_code == 404:
            st.error("⚠️ User not found in database. Please register first.")
            st.session_state.logged_in = False # Force logout
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Could not connect to the backend server.")
    return None

# --- Sidebar (Authentication & Settings) ---
with st.sidebar:
    st.title("✨ AI Assistant")
    st.markdown("---")
    
    if not st.session_state.logged_in:
        st.subheader("Welcome! Please Authenticate")
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        # NOTE: Because your backend doesn't have a /login route, 
        # login here just saves the username to session state. 
        # If the user doesn't exist, the /chat endpoint will catch it and return 404.
        with tab1:
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In", use_container_width=True, type="primary"):
                if login_user:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.messages = [] # clear frontend chat history on new login
                    st.rerun()
                else:
                    st.warning("Please enter a username.")
                    
        with tab2:
            reg_user = st.text_input("New Username", key="reg_user")
            reg_pass = st.text_input("New Password", type="password", key="reg_pass")
            if st.button("Register", use_container_width=True):
                if reg_user and reg_pass:
                    register_user(reg_user, reg_pass)
                else:
                    st.warning("Please fill out all fields.")
    else:
        st.success(f"👤 Logged in as **{st.session_state.username}**")
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = []
            st.rerun()

# --- Main Chat Interface ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>AI Search & Chat Engine</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Log in from the sidebar to begin</h4>", unsafe_allow_html=True)
    
    st.divider()
    st.info("💡 **Pro Tip:** If your message includes the word **'search'**, the AI will browse DuckDuckGo in real-time to answer your question!")
    
else:
    st.title(f"Chat with AI 🤖")
    st.caption("Powered by Groq, LangChain, and DuckDuckGo")
    
    # Display existing chat history from Streamlit session state
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input Box
    if prompt := st.chat_input("Type your message here (include 'search' to browse the web)..."):
        # 1. Display user's prompt in UI
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # 2. Fetch API response with a loading spinner
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = send_chat_message(st.session_state.username, prompt)
                
                if ai_response:
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})