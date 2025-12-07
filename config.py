import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "cat-exam-prep")
    EMBEDDING_MODEL = "text-embedding-3-small"  # Cost-effective for free tier
    CHAT_MODEL = "gpt-3.5-turbo"  # Or gpt-4 if you prefer
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

