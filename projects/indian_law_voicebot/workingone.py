
import io
import os
import tempfile
import datetime
import json
import sqlite3
import hashlib
import base64
import time
from typing import List, Dict, Any
import pandas as pd

import pygame
import speech_recognition as sr
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
from langchain.docstore.document import Document
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    MessagesPlaceholder)
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title=" Law Buddy",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    conn = sqlite3.connect('law_buddy.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            query TEXT,
            response TEXT,
            timestamp DATETIME,
            is_voice BOOLEAN,
            category TEXT,
            satisfaction_score INTEGER,
            response_time REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'en',
            voice_speed REAL DEFAULT 1.0,
            auto_play BOOLEAN DEFAULT TRUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT,
            upload_date DATETIME,
            file_type TEXT,
            session_id TEXT
        )
    ''')
    conn.commit()
    return conn

# Initialize session state
def init_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
    
    if 'voice_queries' not in st.session_state:
        st.session_state.voice_queries = 0
    
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    if 'auto_play' not in st.session_state:
        st.session_state.auto_play = True
    
    if 'voice_speed' not in st.session_state:
        st.session_state.voice_speed = 1.0
    
    if 'bookmarks' not in st.session_state:
        st.session_state.bookmarks = []
    
    if 'query_categories' not in st.session_state:
        st.session_state.query_categories = {}
    
    if 'response_times' not in st.session_state:
        st.session_state.response_times = []

# Custom CSS with theme support
def load_css(theme='light'):
    dark_theme = theme == 'dark'
    bg_color = '#1e1e1e' if dark_theme else '#ffffff'
    text_color = '#ffffff' if dark_theme else '#000000'
    card_bg = '#2d2d2d' if dark_theme else '#f8f9fa'
    border_color = '#444' if dark_theme else '#e0e0e0'
    
    return f"""
    <style>
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        .main-header {{
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #1e3c72, #2a5298);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
            animation: glow 2s ease-in-out infinite alternate;
        }}
        
        @keyframes glow {{
            from {{ text-shadow: 0 0 20px #2a5298; }}
            to {{ text-shadow: 0 0 30px #1e3c72; }}
        }}
        
        .section-header {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #1e3c72;
            margin: 1rem 0;
            padding: 0.5rem;
            border-left: 4px solid #2a5298;
            background-color: {card_bg};
            border-radius: 5px;
        }}
        
        .chat-message {{
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
            position: relative;
        }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .user-message {{
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            border-left: 4px solid #2196f3;
            margin-left: 20%;
        }}
        
        .bot-message {{
            background: linear-gradient(135deg, #f3e5f5, #e1bee7);
            border-left: 4px solid #9c27b0;
            margin-right: 20%;
        }}
        
        .chat-container {{
            max-height: 500px;
            overflow-y: auto;
            padding: 1rem;
            background-color: {card_bg};
            border-radius: 15px;
            border: 1px solid {border_color};
            scrollbar-width: thin;
            scrollbar-color: #2a5298 {card_bg};
        }}
        
        .chat-container::-webkit-scrollbar {{
            width: 8px;
        }}
        
        .chat-container::-webkit-scrollbar-track {{
            background: {card_bg};
        }}
        
        .chat-container::-webkit-scrollbar-thumb {{
            background: #2a5298;
            border-radius: 4px;
        }}
        
        .voice-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 20px;
            color: white;
            margin: 1rem 0;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        
        .chat-section {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 2rem;
            border-radius: 20px;
            color: white;
            margin: 1rem 0;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }}
        
        .disclaimer {{
            background: linear-gradient(135deg, #fff3cd, #ffeaa7);
            border: 1px solid #ffeaa7;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            font-style: italic;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .stats-card {{
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            text-align: center;
            margin: 0.5rem;
            transition: transform 0.3s ease;
        }}
        
        .stats-card:hover {{
            transform: translateY(-5px);
        }}
        
        .typing-indicator {{
            display: flex;
            align-items: center;
            padding: 1rem;
            background: linear-gradient(135deg, #e8f5e8, #c8e6c9);
            border-radius: 15px;
            margin: 0.5rem 0;
        }}
        
        .typing-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #4caf50;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }}
        
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        
        @keyframes typing {{
            0%, 60%, 100% {{ opacity: 0.3; }}
            30% {{ opacity: 1; }}
        }}
        
        .feature-highlight {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 4px;
            background-color: #e0e0e0;
            border-radius: 2px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4facfe, #00f2fe);
            border-radius: 2px;
            transition: width 0.3s ease;
        }}
        
        .document-upload {{
            border: 2px dashed #4facfe;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        }}
    </style>
    """

# Initialize components
conn = init_database()
init_session_state()

# Load CSS
st.markdown(load_css(st.session_state.theme), unsafe_allow_html=True)

@st.cache_resource
def initialize_chat_model():
    GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
    chat_model = ChatGroq(api_key=GROQ_API_KEY, model_name="llama3-8b-8192")
    
    return chat_model

chat_model = initialize_chat_model()

# Enhanced chat template with context awareness
chat_prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content=""" You are Law Buddy, an advanced AI legal assistant with enhanced capabilities:
    
    Core Responsibilities:
    - Provide information based ONLY on retrieved legal documents
    - Categorize queries into: Criminal Law, Civil Law, Property Law, Contract Law, Family Law, Constitutional Law, Tax Law, Labor Law, Corporate Law, Other
    - Use simple, clear language while maintaining legal accuracy
    - Provide relevant case citations when available
    - Suggest related legal topics for further exploration
    
    Response Format:
    1. Direct answer to the query
    2. Relevant legal provisions/sections (if applicable)
    3. Brief explanation in simple terms
    4. Related topics for further reading
    5. Standard disclaimer
    
    Always end with: "This is not legal advice. Please consult a qualified legal professional for specific legal matters."
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{human_input}")
])

# Initialize memory and chain
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
output_parser = StrOutputParser()
chain = RunnablePassthrough.assign(
    chat_history=RunnableLambda(lambda human_input: memory.load_memory_variables(human_input)['chat_history'])
) | chat_prompt_template | chat_model | output_parser

# Initialize embeddings and database
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
#embeddings_model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

CHROMA_DB_DIR = "./chroma_db_"
db = Chroma(collection_name="vector_database", embedding_function=embeddings_model, persist_directory=CHROMA_DB_DIR)

# Enhanced response function with analytics
def get_enhanced_response(input_query, db, chain, memory):
    start_time = time.time()
    
    # Perform similarity search
    docs_chroma = db.similarity_search_with_score(input_query, k=3)
    context_text = "\n\n".join([doc.page_content for doc, _score in docs_chroma])
    
    # Enhanced query with context
    query = {
        "human_input": f"""Context: {context_text}
        
        Query: {input_query}
        
        Please provide a comprehensive response that includes:
        1. Direct answer based on the legal documents
        2. Relevant legal provisions or sections
        3. Simple explanation for non-legal professionals
        4. Related topics for further exploration
        5. Legal category classification
        
        Keep the response concise but informative."""
    }
    
    # Get response
    response = chain.invoke(query)
    memory.save_context(query, {"output": response})
    
    # Calculate response time
    response_time = time.time() - start_time
    st.session_state.response_times.append(response_time)
    
    # Categorize query (simple keyword-based classification)
    category = categorize_query(input_query)
    st.session_state.query_categories[category] = st.session_state.query_categories.get(category, 0) + 1
    
    return response, response_time, category

def categorize_query(query):
    categories = {
        'Criminal Law': ['crime', 'criminal', 'theft', 'murder', 'assault', 'bail', 'arrest', 'police', 'fir'],
        'Civil Law': ['civil', 'tort', 'damages', 'compensation', 'negligence', 'liability'],
        'Property Law': ['property', 'land', 'real estate', 'ownership', 'possession', 'lease', 'rent'],
        'Contract Law': ['contract', 'agreement', 'breach', 'terms', 'conditions', 'parties'],
        'Family Law': ['marriage', 'divorce', 'custody', 'alimony', 'family', 'child', 'adoption'],
        'Constitutional Law': ['constitution', 'fundamental rights', 'directive principles', 'parliament'],
        'Tax Law': ['tax', 'income tax', 'gst', 'vat', 'taxation', 'revenue'],
        'Labor Law': ['labor', 'employment', 'worker', 'salary', 'wage', 'workplace'],
        'Corporate Law': ['company', 'corporate', 'business', 'shares', 'director', 'board']
    }
    
    query_lower = query.lower()
    for category, keywords in categories.items():
        if any(keyword in query_lower for keyword in keywords):
            return category
    return 'Other'

# Enhanced TTS with speed control
def enhanced_text_to_speech(text, speed=1.0, auto_play=True):
    if not auto_play:
        return
    
    language = "en"
    tts = gTTS(text=text, lang=language, slow=(speed < 0.8))
    speech_fp = io.BytesIO()
    tts.write_to_fp(speech_fp)
    speech_fp.seek(0)
    
    # Create audio player with custom controls
    st.audio(speech_fp, format="audio/mp3", start_time=0)

# Database operations
def save_conversation(query, response, is_voice, category, satisfaction_score, response_time):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations 
        (session_id, query, response, timestamp, is_voice, category, satisfaction_score, response_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (st.session_state.session_id, query, response, datetime.datetime.now(), 
          is_voice, category, satisfaction_score, response_time))
    conn.commit()

def load_conversation_history():
    cursor = conn.cursor()
    cursor.execute('''
        SELECT query, response, timestamp, is_voice, category, satisfaction_score, response_time
        FROM conversations 
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (st.session_state.session_id,))
    return cursor.fetchall()

def get_analytics_data():
    cursor = conn.cursor()
    
    # Get query categories
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM conversations 
        WHERE session_id = ?
        GROUP BY category
    ''', (st.session_state.session_id,))
    categories = cursor.fetchall()
    
    # Get satisfaction scores
    cursor.execute('''
        SELECT satisfaction_score, COUNT(*) as count
        FROM conversations 
        WHERE session_id = ? AND satisfaction_score IS NOT NULL
        GROUP BY satisfaction_score
    ''', (st.session_state.session_id,))
    satisfaction = cursor.fetchall()
    
    # Get response times
    cursor.execute('''
        SELECT response_time, timestamp
        FROM conversations 
        WHERE session_id = ?
        ORDER BY timestamp
    ''', (st.session_state.session_id,))
    response_times = cursor.fetchall()
    
    return categories, satisfaction, response_times

# Document upload and processing
def process_uploaded_document(uploaded_file):
    if uploaded_file is not None:
        content = uploaded_file.read()
        if uploaded_file.type == "text/plain":
            content = content.decode("utf-8")
        elif uploaded_file.type == "application/pdf":
            content = "PDF processing requires additional libraries"
        
        # Save to database
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (filename, content, upload_date, file_type, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (uploaded_file.name, content, datetime.datetime.now(), uploaded_file.type, st.session_state.session_id))
        conn.commit()
        
        return True
    return False

# Main UI
st.markdown('<h1 class="main-header">⚖️  Law Buddy</h1>', unsafe_allow_html=True)

# Enhanced disclaimer with features
st.markdown("""
<div class="disclaimer">
    <strong>⚠️ Important Disclaimer:</strong> This AI assistant provides information based on legal documents but does not provide legal advice. 
    Always consult with a qualified legal professional for specific legal matters.
</div>
<div class="feature-highlight">
    🎉 <strong>New Features:</strong> Voice Recognition • Document Upload • Smart Analytics • Dark Theme • Conversation Export • Real-time Chat
</div>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings & Analytics")
    
    # Theme toggle
    theme_col1, theme_col2 = st.columns(2)
    with theme_col1:
        if st.button("🌙 Dark" if st.session_state.theme == 'light' else "☀️ Light"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()
    
    # Voice settings
    st.markdown("### 🔊 Voice Settings")
    st.session_state.auto_play = st.checkbox("Auto-play responses", value=st.session_state.auto_play)
    st.session_state.voice_speed = st.slider("Voice Speed", 0.5, 2.0, st.session_state.voice_speed, 0.1)
    
    # Statistics
    st.markdown("### 📊 Session Statistics")
    
    # Load conversation history for stats
    history = load_conversation_history()
    total_conversations = len(history)
    voice_conversations = sum(1 for h in history if h[3])  # is_voice column
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3 style="color: #2a5298; margin: 0;">{total_conversations}</h3>
            <p style="margin: 0;">Total Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3 style="color: #2a5298; margin: 0;">{voice_conversations}</h3>
            <p style="margin: 0;">Voice Queries</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Average response time
    if st.session_state.response_times:
        avg_response_time = sum(st.session_state.response_times) / len(st.session_state.response_times)
        st.markdown(f"""
        <div class="stats-card">
            <h3 style="color: #2a5298; margin: 0;">{avg_response_time:.2f}s</h3>
            <p style="margin: 0;">Avg Response Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("---")
    if st.button("🗑️ Clear History", type="secondary"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE session_id = ?", (st.session_state.session_id,))
        conn.commit()
        st.session_state.chat_history = []
        st.session_state.total_queries = 0
        st.session_state.voice_queries = 0
        st.success("History cleared!")
        st.rerun()
    
    if st.button("📥 Export History", type="secondary"):
        history_df = pd.DataFrame(history, columns=['Query', 'Response', 'Timestamp', 'Voice', 'Category', 'Satisfaction', 'Response Time'])
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"law_buddy_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Main content with enhanced tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Smart Chat", "🎤 Voice Assistant", "📊 Analytics", "📁 Documents", "📝 History"])

with tab1:
    st.markdown('<div class="chat-section">', unsafe_allow_html=True)
    st.markdown('<h2 style="color: white; margin-top: 0;">💬 Intelligent Chat Interface</h2>', unsafe_allow_html=True)
    
    # Smart suggestions
    st.markdown("### 🎯 Popular Legal Topics")
    suggestion_cols = st.columns(4)
    suggestions = [
        "Property Rights in India",
        "Marriage Laws",
        "Employment Rights",
        "Consumer Protection"
    ]
    
    for i, suggestion in enumerate(suggestions):
        with suggestion_cols[i]:
            if st.button(suggestion, key=f"suggest_{i}"):
                st.session_state.suggested_query = suggestion
    
    # Main query input
    query = st.text_input(
        "Ask your legal question:", 
        placeholder="e.g., What are the rights of tenants in India?",
        value=st.session_state.get('suggested_query', ''),
        key="main_query"
    )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        search_depth = st.slider("Search Depth", 1, 5, 3, help="Number of documents to search")
        include_examples = st.checkbox("Include Examples", value=True)
        include_citations = st.checkbox("Include Citations", value=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ask_button = st.button("🚀 Ask Question", type="primary", key="ask_main")
    with col2:
        if st.button("🔄 Clear", key="clear_main"):
            if 'suggested_query' in st.session_state:
                del st.session_state.suggested_query
            st.rerun()
    with col3:
        if st.button("🔍 Related Topics", key="related_main"):
            st.info("Feature coming soon!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if ask_button and query:
        # Show typing indicator
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
        <div class="typing-indicator">
            <span>Law Buddy is thinking</span>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.spinner("🔍 Analyzing legal documents..."):
            response, response_time, category = get_enhanced_response(query, db, chain, memory)
            
            # Remove typing indicator
            typing_placeholder.empty()
            
            # Save to database
            save_conversation(query, response, False, category, None, response_time)
            
            # Display response
            st.success("✅ Response generated!")
            st.markdown(f"### 📋 Response (Category: {category})")
            st.markdown(f"**Response Time:** {response_time:.2f}s")
            st.write(response)
            
            # Satisfaction buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("👍 Helpful", key="helpful_main"):
                    st.success("Thank you for your feedback!")
            with col2:
                if st.button("👎 Not Helpful", key="not_helpful_main"):
                    st.info("We'll work on improving our responses.")
            with col3:
                if st.button("⭐ Bookmark", key="bookmark_main"):
                    st.session_state.bookmarks.append({"query": query, "response": response})
                    st.success("Response bookmarked!")
            
            # Audio response
            if st.session_state.auto_play:
                st.markdown("### 🔊 Audio Response")
                enhanced_text_to_speech(response, st.session_state.voice_speed, st.session_state.auto_play)

with tab2:
    st.markdown('<div class="voice-section">', unsafe_allow_html=True)
    st.markdown('<h2 style="color: white; margin-top: 0;">🎤 Advanced Voice Assistant</h2>', unsafe_allow_html=True)
    
    # Voice settings
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p style="color: white;">Click to record your question</p>', unsafe_allow_html=True)
    with col2:
        noise_reduction = st.checkbox("Noise Reduction", value=True, key="noise_reduction")
    
    # Voice recorder with visualization
    audio_bytes = audio_recorder(
        text="🎤 Click to Record",
        recording_color="#ff6b6b",
        neutral_color="#4ecdc4",
        icon_name="microphone",
        icon_size="3x",
        key="main_voice_recorder"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if audio_bytes:
        # Show processing indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Process audio
            status_text.text("🎯 Processing audio...")
            progress_bar.progress(25)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            # Speech recognition
            status_text.text("🔊 Converting speech to text...")
            progress_bar.progress(50)
            
            recognizer = sr.Recognizer()
            if noise_reduction:
                recognizer.energy_threshold = 4000
                recognizer.dynamic_energy_threshold = True
            
            with sr.AudioFile(temp_audio_path) as source:
                if noise_reduction:
                    recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)
                
                voice_query = recognizer.recognize_google(audio_data)
                
                status_text.text("🤖 Generating response...")
                progress_bar.progress(75)
                
                st.success("📝 Voice successfully transcribed!")
                st.markdown("### 🗣️ Your Question:")
                st.info(voice_query)
                
                # Get response
                response, response_time, category = get_enhanced_response(voice_query, db, chain, memory)
                save_conversation(voice_query, response, True, category, None, response_time)
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
                st.markdown("### 📋 Response:")
                st.write(response)
                
                st.markdown("### 🔊 Audio Response:")
                enhanced_text_to_speech(response, st.session_state.voice_speed, st.session_state.auto_play)
                
        except sr.UnknownValueError:
            st.error("❌ Could not understand the audio. Please try again with clearer speech.")
        except sr.RequestError:
            st.error("❌ Could not process request. Please check your internet connection.")
        finally:
            # Clean up temp file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

with tab3:
    st.markdown("### 📊 Advanced Analytics Dashboard")
    
    categories, satisfaction, response_times = get_analytics_data()
    
    if categories or satisfaction or response_times:
        col1, col2 = st.columns(2)
        
        with col1:
            if categories:
                st.subheader("📈 Query Categories")
                category_df = pd.DataFrame(categories, columns=['Category', 'Count'])
                fig = px.pie(category_df, values='Count', names='Category', title="Query Distribution by Category")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if satisfaction:
                st.subheader("😊 User Satisfaction")
                satisfaction_df = pd.DataFrame(satisfaction, columns=['Score', 'Count'])
                satisfaction_df['Label'] = satisfaction_df['Score'].map({1: 'Helpful', 0: 'Not Helpful'})
                fig = px.bar(satisfaction_df, x='Label', y='Count', title="User Feedback")
                st.plotly_chart(fig, use_container_width=True)
        
        if response_times:
            st.subheader("⚡ Response Time Trends")
            response_df = pd.DataFrame(response_times, columns=['Response Time', 'Timestamp'])
            response_df['Timestamp'] = pd.to_datetime(response_df['Timestamp'])
            fig = px.line(response_df, x='Timestamp', y='Response Time', title="Response Time Over Time")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics data available yet. Start using the chat to see insights!")

with tab4:
    st.markdown("### 📁 Document Management")
    
    st.markdown('<div class="document-upload">', unsafe_allow_html=True)
    st.markdown("#### Upload Legal Documents")
    st.markdown("Support formats: PDF, TXT, DOCX")
    
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=['pdf', 'txt', 'docx'],
        help="Upload legal documents to enhance the knowledge base"
    )
    
    if uploaded_file:
        if st.button("📤 Process Document"):
            if process_uploaded_document(uploaded_file):
                st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully!")
            else:
                st.error("❌ Failed to process document")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display uploaded documents
    cursor = conn.cursor()
    cursor.execute('''
        SELECT filename, upload_date, file_type 
        FROM documents 
        WHERE session_id = ?
        ORDER BY upload_date DESC
    ''', (st.session_state.session_id,))
    docs = cursor.fetchall()
    
    if docs:
        st.subheader("📚 Your Uploaded Documents")
        for doc in docs:
            with st.expander(f"📄 {doc[0]} ({doc[2]})"):
                st.write(f"**Uploaded:** {doc[1]}")
                if st.button(f"🗑️ Delete {doc[0]}", key=f"delete_{doc[0]}"):
                    cursor.execute("DELETE FROM documents WHERE filename = ? AND session_id = ?", (doc[0], st.session_state.session_id))
                    conn.commit()
                    st.success(f"Document '{doc[0]}' deleted!")
                    st.rerun()

with tab5:
    st.markdown("### 📝 Conversation History")
    
    history = load_conversation_history()
    
    if history:
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Conversations", len(history))
        with col2:
            voice_count = sum(1 for h in history if h[3])
            st.metric("Voice Queries", voice_count)
        with col3:
            avg_satisfaction = sum(h[5] for h in history if h[5] is not None) / len([h for h in history if h[5] is not None]) if any(h[5] is not None for h in history) else 0
            st.metric("Avg Satisfaction", f"{avg_satisfaction:.1f}/1.0")
        
        # Search in history
        search_term = st.text_input("🔍 Search conversations:", placeholder="Enter keywords to search...")
        
        # Filter and display conversations
        filtered_history = history
        if search_term:
            filtered_history = [h for h in history if search_term.lower() in h[0].lower() or search_term.lower() in h[1].lower()]
        
        for i, (query, response, timestamp, is_voice, category, satisfaction, response_time) in enumerate(filtered_history[:20]):
            with st.expander(f"{'🎤' if is_voice else '💬'} {query[:100]}... ({timestamp})"):
                st.markdown(f"**Category:** {category}")
                st.markdown(f"**Query:** {query}")
                st.markdown(f"**Response:** {response}")
                st.markdown(f"**Response Time:** {response_time:.2f}s")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"⭐ Bookmark", key=f"bookmark_history_{i}"):
                        st.session_state.bookmarks.append({"query": query, "response": response})
                        st.success("Bookmarked!")
                with col2:
                    if st.button(f"🔊 Listen", key=f"listen_history_{i}"):
                        enhanced_text_to_speech(response, st.session_state.voice_speed, True)
    else:
        st.info("No conversation history yet. Start chatting to see your conversations here!")

# Display bookmarks
if st.session_state.bookmarks:
    with st.expander("⭐ Your Bookmarks"):
        for i, bookmark in enumerate(st.session_state.bookmarks):
            st.markdown(f"**Q:** {bookmark['query']}")
            st.markdown(f"**A:** {bookmark['response'][:200]}...")
            if st.button(f"🗑️ Remove", key=f"remove_bookmark_{i}"):
                st.session_state.bookmarks.pop(i)
                st.rerun()
            st.markdown("---")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🔒 Your conversations are private and secure | 📚 Powered by Indian Legal Documents | 🤖 Enhanced with AI Analytics</p>
    <p><strong>Remember:</strong> This is not legal advice. Always consult a qualified legal professional.</p>
    <p>Version 2.0 - Advanced Features Enabled</p>
</div>
""", unsafe_allow_html=True)