import logging
from typing import List, Dict, Any
import google.generativeai as genai
from config import Config
from document_processor import DocumentProcessor
from vector_store import VectorStore
from memory_manager import MemoryManager
import uuid


logger = logging.getLogger(__name__)

class RAGChatbot:
    """RAG (Retrieval-Augmented Generation) Chatbot."""
    
    def __init__(self, session_id=None):
        """Initialize the RAG chatbot."""
        Config.validate()
        
        # Configure Gemini
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        #intitialize session and vector store (collection) for memory
        self.session_id = session_id or str(uuid.uuid4())
        self.memory_manager = MemoryManager()
        self.memory_store = VectorStore(collection_name=f"{Config.COLLECTION_NAME}_memory")

        logger.info("RAG Chatbot initialized successfully")
    
    def load_documents(self, file_path: str):
        """
        Load and process documents into the vector store.
        
        Args:
            file_path (str): Path to the document file
        """
        try:
            logger.info(f"Loading documents from: {file_path}")
            
            # Process document
            text_chunks, embeddings = self.document_processor.process_document(file_path)
            
            # Store in vector database
            self.vector_store.add_documents(text_chunks, embeddings)
            
            logger.info("Documents loaded and indexed successfully")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            raise
    
    def _retrieve_context(self, query: str, limit: int = None) -> str:
        """
        Retrieve relevant context for a query.
        
        Args:
            query (str): User query
            limit (int, optional): Number of results to retrieve
            
        Returns:
            str: Retrieved context
        """
        try:
            effective_query = self._rewrite_query_with_history(query)
            query_vector = self.document_processor.embed_query(effective_query)
            
            # Search for relevant documents
            doc_results = self.vector_store.search(query_vector, limit)

            mem_results = self.memory_store.search_with_filter(query_vector, limit, {"session_id": self.session_id, "type": "memory"})
            merged = sorted([{"text": x["text"], "score": x["score"]} for x in doc_results+mem_results],key=lambda x: -x["score"])

            context = "\n\n".join(x["text"] for x in merged[:limit])
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise
    
    def _rewrite_query_with_history(self, query: str) -> str:
        if not self.memory_manager.buffer and not self.memory_manager.summary:
            return query
        prompt = self.memory_manager.build_rewrite_prompt(query)
        response = self.model.generate_content(prompt)
        result = response.text.strip()
        return result if result and len(result) > 5 else query





    def _generate_response(self, query: str, context: str) -> str:
        """
        Generate response using Gemini.
        
        Args:
            query (str): User query
            context (str): Retrieved context
            
        Returns:
            str: Generated response
        """
        try:
            history_text = self.memory_manager.get_buffer_text()
            prompt = f"""You are a helpful assistant. Use summary, history, and the retrieved context.

Summary:
{self.memory_manager.summary}

Recent history:
{history_text}

Context:
{context}

Question: {query}
Answer:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise



    def _update_memory(self, query, answer):
        # Update summary
        prompt = self.memory_manager.build_summary_prompt(query, answer)
        response = self.model.generate_content(prompt)
        self.memory_manager.summary = response.text.strip()

        # Extract facts and store
        facts_prompt = self.memory_manager.build_facts_prompt(query, answer)
        facts_resp = self.model.generate_content(facts_prompt)
        facts_lines = [
            l.strip("•- ").strip()
            for l in facts_resp.text.splitlines()
            if l.strip() and "NONE" not in l.upper()
        ]
        if facts_lines:
            embeddings = list(self.document_processor.embedding_model.embed(facts_lines))
            metas = [{"session_id": self.session_id, "type": "memory"}] * len(facts_lines)
            self.memory_store.add_documents(facts_lines, embeddings, metas)

        # Buffer turn
        self.memory_manager.append_turn(query, answer)

    # Then call _update_memory(query, response) at the end of chat()






    def chat(self, query: str) -> Dict[str, Any]:
        """
        Process a chat query and return response with metadata.
        
        Args:
            query (str): User query
            
        Returns:
            Dict[str, Any]: Response with metadata
        """
        try:
            logger.info(f"Processing query: {query}")
            
            context = self._retrieve_context(query)
            
            response = self._generate_response(query, context)

            self._update_memory(query, response)

            
            logger.info("Query processed successfully")
            
            return {
                "query": query,
                "response": response,
                "context": context,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "query": query,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "context": "",
                "success": False,
                "error": str(e)
            }
    
    def simple_chat(self, query: str) -> str:
        """
        Simple chat interface that returns just the response text.
        
        Args:
            query (str): User query
            
        Returns:
            str: Response text
        """
        result = self.chat(query)
        return result["response"]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get chatbot status and collection info.
        
        Returns:
            Dict[str, Any]: Status information
        """
        try:
            collection_info = self.vector_store.get_collection_info()
            return {
                "status": "ready",
                "collection": collection_info,
                "model": Config.GEMINI_MODEL,
                "embedding_model": Config.EMBEDDING_MODEL
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }