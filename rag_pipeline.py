from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from pinecone import Pinecone
import config

class RAGPipeline:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=config.Config.EMBEDDING_MODEL,
            openai_api_key=config.Config.OPENAI_API_KEY
        )
        
        self.llm = ChatOpenAI(
            model_name=config.Config.CHAT_MODEL,
            temperature=0.7,
            openai_api_key=config.Config.OPENAI_API_KEY
        )
        
        # Check if index exists before trying to connect
        pc = Pinecone(api_key=config.Config.PINECONE_API_KEY)
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        
        if config.Config.PINECONE_INDEX_NAME not in existing_indexes:
            raise ValueError(
                f"Pinecone index '{config.Config.PINECONE_INDEX_NAME}' does not exist. "
                "Please process documents first by clicking 'Process Documents' in the sidebar."
            )
        
        self.vectorstore = PineconeVectorStore(
            index_name=config.Config.PINECONE_INDEX_NAME,
            embedding=self.embeddings
        )
        
        # Custom prompt for CAT exam context
        self.prompt_template = """You are an expert tutor for CAT (Common Admission Test) exam preparation. 
        Use the following pieces of context to answer the student's question about CAT exam preparation.
        If you don't know the answer based on the context, say that you don't know, but try to be helpful.
        
        Context: {context}
        
        Question: {question}
        
        Provide a clear, detailed answer that helps the student understand the concept better:"""
        
        self.qa_prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}  # Retrieve top 3 relevant chunks
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.qa_prompt}
        )
    
    def query(self, question: str):
        """Query the RAG pipeline"""
        result = self.qa_chain({"query": question})
        return {
            "answer": result["result"],
            "sources": [doc.metadata.get("source", "Unknown") for doc in result["source_documents"]]
        }

