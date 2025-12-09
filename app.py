import streamlit as st
import os
from document_processor import DocumentProcessor
from rag_pipeline import RAGPipeline
from database import Database
from question_extractor import QuestionExtractor
from adaptive_selector import AdaptiveQuestionSelector
import config
import time
import pandas as pd
import plotly.express as px

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

# Initialize database
db = Database()

# Get or create user (using session ID)
if "user_id" not in st.session_state:
    import uuid
    st.session_state.user_id = str(uuid.uuid4())
    db.get_or_create_user(st.session_state.user_id)

user_id = st.session_state.user_id

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "page" not in st.session_state:
    st.session_state.page = "Chat"

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

# Navigation
st.markdown('<h1 class="main-header">📚 CAT Exam Prep Platform</h1>', unsafe_allow_html=True)

# Page selection
page = st.radio(
    "Select Mode:",
    ["💬 Chat Assistant", "📊 Dashboard", "🎯 Adaptive Practice", "📝 Mock Test", "📥 Extract Questions"],
    horizontal=True,
    key="page_selector"
)

st.divider()

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

# Route to different pages based on selection
if page == "💬 Chat Assistant":
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

elif page == "📊 Dashboard":
    st.header("📊 Progress Dashboard")
    
    stats = db.get_user_stats(user_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Attempts", stats['total_attempts'])
    with col2:
        st.metric("Accuracy", f"{stats['accuracy']:.1f}%")
    with col3:
        st.metric("Avg Time/Question", f"{stats['avg_time']:.0f}s")
    with col4:
        st.metric("🔥 Streak", f"{stats['streak']} days")
    
    st.divider()
    
    # Topic-wise performance
    if stats['topic_stats']:
        st.subheader("📈 Topic-wise Performance")
        
        topic_df = pd.DataFrame(stats['topic_stats'])
        topic_df['accuracy'] = (topic_df['correct'] / topic_df['attempts'] * 100).round(1)
        topic_df = topic_df.sort_values('accuracy')
        
        # Bar chart
        fig = px.bar(
            topic_df,
            x='topic_name',
            y='accuracy',
            title='Accuracy by Topic',
            labels={'topic_name': 'Topic', 'accuracy': 'Accuracy (%)'},
            color='accuracy',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Weak topics
        weak_topics = topic_df[topic_df['accuracy'] < 60]
        if not weak_topics.empty:
            st.warning(f"⚠️ **Areas needing improvement:** {', '.join(weak_topics['topic_name'].tolist())}")
    
    # Recent activity
    st.subheader("📅 Recent Activity")
    attempts = db.get_user_attempts(user_id, limit=10)
    if attempts:
        attempts_df = pd.DataFrame(attempts)
        attempts_df['result'] = attempts_df['is_correct'].apply(lambda x: '✅ Correct' if x == 1 else '❌ Wrong')
        attempts_df['attempt_at'] = pd.to_datetime(attempts_df['attempt_at'])
        st.dataframe(
            attempts_df[['question_text', 'topic_name', 'result', 'time_taken_sec', 'attempt_at']].head(10),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No attempts yet. Start practicing to see your progress!")

elif page == "🎯 Adaptive Practice":
    st.header("🎯 Adaptive Practice")
    
    selector = AdaptiveQuestionSelector(db)
    
    # Get next question
    if st.session_state.current_question is None or st.button("🔄 Get New Question"):
        st.session_state.current_question = selector.select_next_question(user_id)
        st.session_state.question_start_time = time.time()
        st.session_state.practice_mode = True
    
    if st.session_state.current_question:
        q = st.session_state.current_question
        
        # Show question
        st.subheader(f"Question (Difficulty: {q['difficulty_score']:.1f}/5.0)")
        st.write(q['question_text'])
        
        # Show options
        selected_answer = st.radio(
            "Select your answer:",
            options=q['options'],
            key="practice_answer"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Submit Answer", type="primary"):
                time_taken = int(time.time() - st.session_state.question_start_time)
                correct_answer = q['correct_answer']
                is_correct = selected_answer.startswith(correct_answer) if correct_answer else False
                
                # Record attempt
                db.record_attempt(
                    user_id=user_id,
                    question_id=q['id'],
                    is_correct=is_correct,
                    time_taken_sec=time_taken,
                    user_answer=selected_answer
                )
                
                # Show result
                if is_correct:
                    st.success("🎉 Correct!")
                else:
                    st.error(f"❌ Wrong! Correct answer is: {correct_answer}")
                
                if q.get('explanation'):
                    st.info(f"💡 **Explanation:** {q['explanation']}")
                
                st.metric("Time taken", f"{time_taken}s")
                
                # Reset for next question
                st.session_state.current_question = None
                st.rerun()
        
        with col2:
            if st.button("⏭️ Skip Question"):
                st.session_state.current_question = None
                st.rerun()
        
        # Show timer
        if st.session_state.question_start_time:
            elapsed = int(time.time() - st.session_state.question_start_time)
            st.caption(f"⏱️ Time elapsed: {elapsed}s")
    else:
        st.info("Click 'Get New Question' to start practicing!")

elif page == "📝 Mock Test":
    st.header("📝 Mock Test")
    
    if not st.session_state.get("test_mode", False):
        # Test configuration
        col1, col2 = st.columns(2)
        with col1:
            num_questions = st.number_input("Number of questions", min_value=5, max_value=50, value=10)
        with col2:
            test_type = st.selectbox("Test Type", ["Full Test", "Quantitative Only", "Verbal Only", "Mixed"])
        
        if st.button("🚀 Start Mock Test", type="primary"):
            # Get questions
            all_questions = db.get_all_questions()
            if len(all_questions) < num_questions:
                st.error(f"Not enough questions in database. Need {num_questions}, have {len(all_questions)}")
            else:
                import random
                st.session_state.test_questions = random.sample(all_questions, num_questions)
                st.session_state.test_current_index = 0
                st.session_state.test_start_time = time.time()
                st.session_state.test_mode = True
                st.session_state.test_id = db.create_test(user_id, test_type, num_questions)
                st.rerun()
    else:
        # Test in progress
        if st.session_state.test_current_index < len(st.session_state.test_questions):
            q = st.session_state.test_questions[st.session_state.test_current_index]
            progress = (st.session_state.test_current_index + 1) / len(st.session_state.test_questions)
            
            st.progress(progress)
            st.caption(f"Question {st.session_state.test_current_index + 1} of {len(st.session_state.test_questions)}")
            
            st.subheader("Question")
            st.write(q['question_text'])
            
            selected_answer = st.radio(
                "Select your answer:",
                options=q['options'],
                key=f"test_answer_{st.session_state.test_current_index}"
            )
            
            if st.button("Next Question", type="primary"):
                # Record answer
                time_taken = int(time.time() - st.session_state.test_start_time)
                db.record_attempt(
                    user_id=user_id,
                    question_id=q['id'],
                    is_correct=False,  # Will update later
                    time_taken_sec=time_taken,
                    user_answer=selected_answer,
                    test_id=st.session_state.test_id
                )
                
                st.session_state.test_current_index += 1
                st.rerun()
        else:
            # Test completed
            st.success("🎉 Test Completed!")
            
            # Calculate score
            test_attempts = [a for a in db.get_user_attempts(user_id, limit=1000) 
                           if a.get('test_id') == st.session_state.test_id]
            
            correct = 0
            for attempt in test_attempts:
                q = db.get_question(attempt['question_id'])
                if q and attempt['user_answer'].startswith(q['correct_answer']):
                    correct += 1
            
            total_time = int(time.time() - st.session_state.test_start_time)
            score = (correct / len(st.session_state.test_questions)) * 100
            
            db.complete_test(st.session_state.test_id, correct, total_time)
            
            st.metric("Score", f"{correct}/{len(st.session_state.test_questions)} ({score:.1f}%)")
            st.metric("Time taken", f"{total_time // 60}m {total_time % 60}s")
            
            if st.button("🔄 Take Another Test"):
                st.session_state.test_mode = False
                st.session_state.test_questions = []
                st.session_state.test_current_index = 0
                st.session_state.test_id = None
                st.rerun()

elif page == "📥 Extract Questions":
    st.header("📥 Extract Questions from Documents")
    
    st.info("Upload PDF files containing CAT exam questions. The system will extract questions and add them to the question bank.")
    
    uploaded_files = st.file_uploader(
        "Upload PDF files with questions",
        type=['pdf'],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("🔍 Extract Questions", type="primary"):
        extractor = QuestionExtractor()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_questions = 0
        
        for idx, uploaded_file in enumerate(uploaded_files):
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                status_text.text(f"Processing {uploaded_file.name}...")
                questions, errors = extractor.extract_questions_from_pdf(temp_path)
                
                # Show any errors
                if errors:
                    with st.expander(f"⚠️ Warnings for {uploaded_file.name}"):
                        for err in errors[:5]:  # Show first 5 errors
                            st.text(err)
                        if len(errors) > 5:
                            st.text(f"... and {len(errors) - 5} more warnings")
                
                if not questions:
                    st.warning(f"⚠️ No questions extracted from {uploaded_file.name}. The PDF might not contain questions in a recognizable format, or the text extraction failed.")
                    continue
                
                # Add questions to database
                added_count = 0
                failed_count = 0
                for q in questions:
                    try:
                        difficulty = extractor.score_difficulty(q)
                        db.add_question(
                            topic_name=q.get('topic', 'General'),
                            question_text=q['question_text'],
                            options=q.get('options', []),
                            correct_answer=q.get('correct_answer', 'A'),
                            explanation=q.get('explanation', ''),
                            difficulty_score=difficulty,
                            estimated_time_sec=120,
                            source_document=q.get('source_document', uploaded_file.name),
                            source_page=q.get('source_page', 0)
                        )
                        added_count += 1
                    except Exception as e:
                        failed_count += 1
                        st.warning(f"Error adding question: {str(e)[:100]}")
                        continue
                
                total_questions += added_count
                if added_count > 0:
                    st.success(f"✅ Extracted and added {added_count} questions from {uploaded_file.name}")
                if failed_count > 0:
                    st.warning(f"⚠️ Failed to add {failed_count} questions from {uploaded_file.name}")
                
            except Exception as e:
                import traceback
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                with st.expander("Error details"):
                    st.code(traceback.format_exc())
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        if total_questions > 0:
            st.success(f"🎉 Successfully added {total_questions} questions to the question bank!")
            status_text.empty()
            progress_bar.empty()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with ❤️ for CAT aspirants</div>",
    unsafe_allow_html=True
)

