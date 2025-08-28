import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for the RAG chatbot."""
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    CHUNK_TOKENIZER = "sentence-transformers/all-MiniLM-L6-v2"
    GEMINI_MODEL = "gemma-3-27b-it"
    
    # Chunking parameters
    MAX_TOKENS = 256
    
    # Vector store settings
    COLLECTION_NAME = "Simple_RAG_Qdrant"
    QDRANT_URL = "https://0ad9e58e-aee3-4dda-b368-3807f55273d4.eu-central-1-0.aws.cloud.qdrant.io:6333"  # Use ":memory:" for in-memory, or provide URL for persistent storage
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")    
    # Search parameters
    RETRIEVAL_LIMIT = 4
    
    # Default document path
    DEFAULT_DOCUMENT_PATH = "data/answers_to_developer_questions.pdf"
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required. Please set it in your .env file.")
        if not cls.QDRANT_API_KEY:
            raise ValueError("QDRANT_API_KEY environment variable is required.")
        return True