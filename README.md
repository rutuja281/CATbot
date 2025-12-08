# CAT Exam Prep RAG Chatbot

A Retrieval-Augmented Generation chatbot for CAT exam preparation using Pinecone (free tier) and OpenAI.

## Features

- 📚 Document ingestion from PDFs
- 🔍 Vector storage in Pinecone (free tier)
- 💬 Interactive web UI with Streamlit
- 🎯 RAG-based question answering
- 📖 Source citation for answers

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=cat-exam-prep
```

**Get your API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Pinecone: https://app.pinecone.io/ (sign up for free tier)


### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`


### 4. Add Documents

Place your CAT exam preparation PDFs in the Document Management section:
- Quantitative Aptitude materials
- Verbal Ability resources
- Data Interpretation guides
- Previous year papers
- Study materials

## Usage

1. **Configure API Keys**: Enter your OpenAI and Pinecone API keys in the sidebar
2. **Process Documents**: Click "Process Documents" to ingest PDFs from the `data/` folder
3. **Start Chatting**: Ask questions about CAT exam preparation!

## Free Tier Limits

- **Pinecone**: 1 index, 100K vectors (free tier)
- **OpenAI**: Pay-as-you-go (text-embedding-3-small is cost-effective)

## Project Structure

```
CATbot/
├── app.py                 # Streamlit UI
├── config.py             # Configuration
├── document_processor.py # PDF processing and indexing
├── rag_pipeline.py       # RAG query pipeline
├── requirements.txt      # Dependencies
├── .env                  # API keys (create this)
├── .env.example         # Example env file
├── README.md            # This file
└── data/                # Place PDFs here
```

## Troubleshooting

- **API Key Errors**: Make sure your `.env` file is in the root directory
- **Pinecone Connection**: Verify your Pinecone environment region
- **No Documents**: Ensure PDFs are in the `data/` folder before processing
- **Import Errors**: Run `pip install -r requirements.txt` in a virtual env


