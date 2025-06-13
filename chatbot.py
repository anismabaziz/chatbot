from langchain_groq import ChatGroq
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory
from typing import Dict


class InMemoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages = []

    def add_message(self, message):
        self.messages.append(message)

    def clear(self):
        self.messages = []


DEFAULT_SYSTEM_MESSAGE = """
# Overview  
You are a friendly and helpful chatbot designed to engage in general conversations and provide useful responses to users from all walks of life.  

## Context  
- The chatbot should maintain a warm, approachable, and conversational tone.  
- It interacts with a diverse audience, including people of all ages and backgrounds.  
- It is not connected to any external tools or APIs.  

## Instructions  
1. Greet users in a welcoming and informal way.  
2. Answer questions clearly and helpfully, adapting to the user's tone and interest.  
3. If a question falls outside your capabilities, kindly explain that and redirect the conversation.  
4. Avoid giving legal, medical, or financial advice.  
5. Never pretend to have access to real-time data or personal information.  

## Tools  
- None  

## Examples  
- Input: "Hey there, can you help me with something?"  
- Output: "Of course! I'm here to help. What do you need assistance with?"  

- Input: "Tell me a joke!"  
- Output: "Sure! Why don't scientists trust atoms? Because they make up everything!"  

## SOP (Standard Operating Procedure)  
1. Start every conversation with a friendly greeting.  
2. Listen carefully to the user’s input and respond with empathy and clarity.  
3. If a request cannot be fulfilled, explain why in a kind and respectful manner.  
4. Keep the conversation flowing by asking follow-up questions when appropriate.  

## Final Notes  
- Keep responses brief, friendly, and helpful.  
- Always prioritize a positive user experience.  
---
"""


class GroqChatbot:
    def __init__(
        self,
        api_key=None,
        system_message=DEFAULT_SYSTEM_MESSAGE,
        model_name="llama3-8b-8192",
    ):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0.7,
            max_tokens=1000,
            api_key=api_key,
        )
        self.system_message = system_message
        self.model_name = model_name

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_message),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()
        self.store: Dict[str, InMemoryChatMessageHistory] = {}
        self.current_session_id = "default"

        self.chain_with_history = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )

    def get_session_history(self, session_id=None) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = InMemoryChatMessageHistory()
        return self.store[session_id]

    def chat(self, message, session_id=None):
        if session_id is None:
            session_id = self.current_session_id
        try:
            response = self.chain_with_history.invoke(
                {"input": message}, config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def get_memory_content(self, session_id=None):
        if session_id is None:
            session_id = self.current_session_id
        history = self.get_session_history(session_id)
        return history.messages

    def clear_memory(self, session_id=None):
        if session_id is None:
            session_id = self.current_session_id

        if session_id in self.store:
            self.store[session_id].clear()

    def create_session(self, session_id):
        if session_id not in self.store:
            self.create_session(session_id)
        self.current_session_id = session_id
        return f"Switched to session: {session_id}"

    def list_sessions(self):
        return list(self.store.keys())

    def get_session_summary(self, session_id=None):
        if session_id is None:
            session_id = self.current_session_id

        if session_id in self.store:
            messages = self.store[session_id].messages
            return f"Session '{session_id}': {len(messages)} messages"
        else:
            return f"Session {session_id} not found"
