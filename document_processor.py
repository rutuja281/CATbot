import os
from typing import List
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import config

class DocumentProcessor:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=config.Config.EMBEDDING_MODEL,
            openai_api_key=config.Config.OPENAI_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.Config.CHUNK_SIZE,
            chunk_overlap=config.Config.CHUNK_OVERLAP,
            length_function=len,
        )
        
    def initialize_pinecone(self):
        """Initialize Pinecone index"""
        try:
            pc = Pinecone(api_key=config.Config.PINECONE_API_KEY)
            
            # Check if index exists
            try:
                existing_indexes = [idx.name for idx in pc.list_indexes()]
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "UNAUTHORIZED" in error_msg:
                    return f"✗ Authentication failed: Invalid Pinecone API key. Please check your API key in the .env file."
                elif "403" in error_msg or "FORBIDDEN" in error_msg:
                    return f"✗ Access denied: Your API key doesn't have permission to list indexes."
                else:
                    return f"✗ Error listing indexes: {error_msg}"
            
            if config.Config.PINECONE_INDEX_NAME not in existing_indexes:
                # Create index with free tier specs
                try:
                    # Parse region - Pinecone free tier uses format like "us-east-1"
                    region = config.Config.PINECONE_ENVIRONMENT
                    # Remove "-aws" suffix if present
                    if region.endswith("-aws"):
                        region = region[:-4]
                    
                    # For free tier, use serverless spec
                    pc.create_index(
                        name=config.Config.PINECONE_INDEX_NAME,
                        dimension=1536,  # text-embedding-3-small dimension
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region=region
                        )
                    )
                    return f"✓ Created index: {config.Config.PINECONE_INDEX_NAME} in region {region}"
                except Exception as e:
                    error_str = str(e)
                    error_lower = error_str.lower()
                    
                    # Provide specific error messages
                    if "401" in error_str or "unauthorized" in error_lower:
                        return f"✗ Authentication failed: Invalid Pinecone API key."
                    elif "403" in error_str or "forbidden" in error_lower:
                        return f"✗ Access denied: Your API key doesn't have permission to create indexes."
                    elif "404" in error_str or "not found" in error_lower:
                        # Try alternative region or method
                        try:
                            # Try with just the region name without cloud specification
                            pc.create_index(
                                name=config.Config.PINECONE_INDEX_NAME,
                                dimension=1536,
                                metric="cosine",
                                spec=ServerlessSpec(region=region)
                            )
                            return f"✓ Created index: {config.Config.PINECONE_INDEX_NAME}"
                        except Exception as e2:
                            return f"✗ Error creating index (404): The region '{region}' might be incorrect. Common regions: 'us-east-1', 'us-west-2', 'eu-west-1'. Check your Pinecone dashboard for the correct region. Error: {str(e2)[:200]}"
                    elif "already exists" in error_lower or "duplicate" in error_lower:
                        return f"✓ Index {config.Config.PINECONE_INDEX_NAME} already exists"
                    else:
                        return f"✗ Error creating index: {error_str[:300]}"
            else:
                return f"✓ Index {config.Config.PINECONE_INDEX_NAME} already exists"
        except Exception as e:
            error_str = str(e)
            if "api_key" in error_str.lower() or "key" in error_str.lower():
                return f"✗ Error: Invalid or missing Pinecone API key. Please check your .env file."
            else:
                return f"✗ Error initializing Pinecone: {str(e)[:300]}"
        
    def load_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    
    def process_documents(self, data_dir: str = "data"):
        """Process all documents in the data directory"""
        status_messages = []
        status_messages.append(self.initialize_pinecone())
        
        documents = []
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            return status_messages + ["No data directory found. Created empty 'data' folder. Please add PDF files."]
        
        pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            return status_messages + ["No PDF files found in the data directory."]
        
        for filename in pdf_files:
            file_path = os.path.join(data_dir, filename)
            status_messages.append(f"Processing {filename}...")
            try:
                text = self.load_pdf(file_path)
                
                # Split into chunks
                chunks = self.text_splitter.create_documents([text])
                chunks = self.text_splitter.split_documents(chunks)
                
                # Add metadata
                for chunk in chunks:
                    chunk.metadata['source'] = filename
                
                documents.extend(chunks)
                status_messages.append(f"✓ Processed {len(chunks)} chunks from {filename}")
            except Exception as e:
                status_messages.append(f"✗ Error processing {filename}: {str(e)}")
        
        if documents:
            # Store in Pinecone
            try:
                vectorstore = PineconeVectorStore.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    index_name=config.Config.PINECONE_INDEX_NAME
                )
                status_messages.append(f"✓ Successfully indexed {len(documents)} document chunks")
            except Exception as e:
                status_messages.append(f"✗ Error indexing documents: {str(e)}")
        else:
            status_messages.append("No documents were processed successfully")
        
        return status_messages

