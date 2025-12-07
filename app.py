import streamlit as st
import os
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
import config

# Page configuration
st.set_page_config(
    page_title="CAT Exam Prep Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False

def initialize_rag():
    """Initialize RAG pipeline"""
    try:
        if config.Config.OPENAI_API_KEY and config.Config.PINECONE_API_KEY:
            st.session_state.rag_pipeline = RAGPipeline()
            st.session_state.initialized = True
            return True
        else:
            return False
    except ValueError as e:
        # Index doesn't exist - this is expected before processing documents
        st.warning(f"⚠️ {str(e)}")
        return False
    except Exception as e:
        error_msg = str(e)
        if "NOT_FOUND" in error_msg or "not found" in error_msg.lower():
            st.warning(
                "⚠️ Pinecone index not found. Please upload PDF files and click 'Process Documents' "
                "in the sidebar to create the index first."
            )
        else:
            st.error(f"❌ Error initializing RAG pipeline: {str(e)}")
        return False

def process_documents():
    """Process documents and return status"""
    try:
        processor = DocumentProcessor()
        return processor.process_documents()
    except Exception as e:
        return [f"Error: {str(e)}"]

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.subheader("API Configuration")
    openai_key = st.text_input("OpenAI API Key", type="password", value=config.Config.OPENAI_API_KEY or "")
    pinecone_key = st.text_input("Pinecone API Key", type="password", value=config.Config.PINECONE_API_KEY or "")
    
    if st.button("Save API Keys"):
        if openai_key and pinecone_key:
            # Update config (in production, save to .env file)
            config.Config.OPENAI_API_KEY = openai_key
            config.Config.PINECONE_API_KEY = pinecone_key
            st.success("API keys saved! Please refresh the page.")
        else:
            st.error("Please enter both API keys")
    
    st.divider()
    
    st.subheader("Document Management")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload CAT exam preparation PDFs"
    )
    
    if uploaded_files:
        if st.button("💾 Save Uploaded Files"):
            os.makedirs("data", exist_ok=True)
            saved_files = []
            for uploaded_file in uploaded_files:
                file_path = os.path.join("data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)
            st.success(f"✅ Saved {len(saved_files)} file(s): {', '.join(saved_files)}")
    
    st.text("---OR---")
    
    if st.button("📄 Process Documents"):
        with st.spinner("Processing documents..."):
            status_messages = process_documents()
            for msg in status_messages:
                st.text(msg)
            # After processing, reset initialization so user can reinitialize
            if any("Successfully indexed" in msg for msg in status_messages):
                st.session_state.initialized = False
                st.session_state.rag_pipeline = None
                st.success("✅ Documents processed! Click '🚀 Initialize Chatbot' in the main area to start chatting.")
    
    st.divider()
    
    st.divider()
    
    st.subheader("Pinecone Setup Help")
    with st.expander("🔧 Troubleshooting Pinecone 404 Errors"):
        st.markdown("""
        **If you get a 404 error when processing documents:**
        
        1. **Check your Pinecone region:**
           - Go to [Pinecone Dashboard](https://app.pinecone.io/)
           - Your region is shown in the URL or index settings
           - Common regions: `us-east-1`, `us-west-2`, `eu-west-1`
           - Update `PINECONE_ENVIRONMENT` in your `.env` file
        
        2. **Verify API Key:**
           - Make sure your API key is correct
           - Free tier API keys start with `pcsk_`
        
        3. **Check Index Limits:**
           - Free tier allows 1 index
           - Delete old indexes if needed
        """)
    
    st.divider()
    
    st.subheader("About")
    st.info("""
    **CAT Exam Prep Chatbot**
    
    A RAG-powered chatbot for CAT exam preparation.
    
    **Steps:**
    1. Add your API keys
    2. Add PDF files using the uploader above
    3. Click "Process Documents"
    4. Click "Initialize Chatbot" in main area
    5. Start chatting!
    """)

# Main content
st.markdown('<h1 class="main-header">📚 CAT Exam Prep Chatbot</h1>', unsafe_allow_html=True)

# Initialize RAG if not already done
if not st.session_state.initialized:
    if config.Config.OPENAI_API_KEY and config.Config.PINECONE_API_KEY:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("📋 **Setup Required:** Upload PDF files and process them first, then click the button below to initialize the chatbot.")
        with col2:
            if st.button("🚀 Initialize Chatbot", type="primary", use_container_width=True):
                with st.spinner("Initializing chatbot..."):
                    if initialize_rag():
                        st.success("✅ Chatbot initialized successfully!")
                        st.rerun()
                    # Error message is already shown in initialize_rag()
    else:
        st.warning("⚠️ Please configure your API keys in the sidebar to start using the chatbot.")

# Chat interface
if st.session_state.initialized and st.session_state.rag_pipeline:
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in set(message["sources"]):
                            st.text(f"• {source}")
    
    # Chat input
    if prompt := st.chat_input("Ask a question about CAT exam preparation..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.rag_pipeline.query(prompt)
                    st.markdown(response["answer"])
                    
                    if response["sources"]:
                        with st.expander("📚 Sources"):
                            for source in set(response["sources"]):
                                st.text(f"• {source}")
                    
                    # Add bot message to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "sources": response["sources"]
                    })
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

else:
    st.info("👆 Configure your API keys in the sidebar to get started!")
    
    # Show example questions
    st.subheader("Example Questions You Can Ask:")
    example_questions = [
        "What are the key topics in Quantitative Aptitude for CAT?",
        "How should I prepare for Data Interpretation?",
        "What is the best strategy for Verbal Ability section?",
        "Explain the concept of time and work problems",
        "What are the important formulas for geometry?"
    ]
    
    for i, q in enumerate(example_questions, 1):
        st.text(f"{i}. {q}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with ❤️ for CAT aspirants</div>",
    unsafe_allow_html=True
)

