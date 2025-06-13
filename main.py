import streamlit as st
import os
from chatbot import GroqChatbot

# Page configuration
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
if "current_session" not in st.session_state:
    st.session_state.current_session = "default"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chatbot_initialized" not in st.session_state:
    st.session_state.chatbot_initialized = False

# Sidebar for configuration and session management
with st.sidebar:
    st.header("🤖 Chatbot Configuration")

    # API Key input
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Enter your Groq API key",
    )

    # Model selection
    model_options = [
        "llama3-8b-8192",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
    ]
    selected_model = st.selectbox("Select Model", model_options, index=0)

    # Initialize chatbot button
    if st.button("Initialize Chatbot", type="primary"):
        if api_key:
            try:
                st.session_state.chatbot = GroqChatbot(
                    api_key=api_key, model_name=selected_model
                )
                st.session_state.chatbot_initialized = True
                st.success("Chatbot initialized successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize chatbot: {str(e)}")
        else:
            st.error("Please enter your Groq API key")

    st.divider()

    # Session management (only show if chatbot is initialized)
    if st.session_state.chatbot_initialized:
        st.header("📋 Session Management")

        # Current session info
        st.info(f"**Current Session:** {st.session_state.current_session}")

        # Create new session
        new_session_name = st.text_input("New Session Name")
        if st.button("Create New Session"):
            if new_session_name:
                st.session_state.chatbot.create_session(new_session_name)
                st.session_state.current_session = new_session_name
                st.session_state.messages = []
                st.success(f"Created session: {new_session_name}")
                st.rerun()
            else:
                st.error("Please enter a session name")

        # List existing sessions
        if st.session_state.chatbot:
            sessions = st.session_state.chatbot.list_sessions()
            if sessions:
                st.subheader("Existing Sessions")
                for session in sessions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"Switch to {session}", key=f"switch_{session}"):
                            st.session_state.current_session = session
                            st.session_state.chatbot.current_session_id = session
                            # Load messages for this session
                            session_messages = (
                                st.session_state.chatbot.get_memory_content(session)
                            )
                            st.session_state.messages = []
                            for msg in session_messages:
                                if hasattr(msg, "content"):
                                    role = (
                                        "user" if msg.type == "human" else "assistant"
                                    )
                                    st.session_state.messages.append(
                                        {"role": role, "content": msg.content}
                                    )
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"clear_{session}", help="Clear session"):
                            st.session_state.chatbot.clear_memory(session)
                            if session == st.session_state.current_session:
                                st.session_state.messages = []
                            st.success(f"Cleared session: {session}")
                            st.rerun()

# Main chat interface
st.title("🤖 AI Chatbot with Sessions")

if not st.session_state.chatbot_initialized:
    st.info(
        "👈 Please configure and initialize the chatbot in the sidebar to start chatting!"
    )
else:
    # Create a container for the chat messages
    chat_container = st.container()

    # Display chat messages using st.chat_message
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Chat input
    prompt = st.chat_input("Type your message here...")

    # Process the input if there is one
    if prompt:
        # Add and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)

        # Get bot response
        with st.spinner("Bot is thinking..."):
            response = st.session_state.chatbot.chat(
                prompt, st.session_state.current_session
            )

        # Add and display bot response
        st.session_state.messages.append({"role": "assistant", "content": response})
        with chat_container:
            with st.chat_message("assistant"):
                st.write(response)

        st.rerun()

    # Additional controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Clear Current Session"):
            st.session_state.chatbot.clear_memory(st.session_state.current_session)
            st.session_state.messages = []
            st.success("Session cleared!")
            st.rerun()

    with col2:
        if st.button("Show Session Info"):
            summary = st.session_state.chatbot.get_session_summary(
                st.session_state.current_session
            )
            st.info(summary)

    with col3:
        if st.button("Export Chat History"):
            if st.session_state.messages:
                chat_export = "\n".join(
                    [
                        f"{msg['role'].title()}: {msg['content']}"
                        for msg in st.session_state.messages
                    ]
                )
                st.download_button(
                    label="Download Chat",
                    data=chat_export,
                    file_name=f"chat_history_{st.session_state.current_session}.txt",
                    mime="text/plain",
                )
            else:
                st.warning("No chat history to export")
