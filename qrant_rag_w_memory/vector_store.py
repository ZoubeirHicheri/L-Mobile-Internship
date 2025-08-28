import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    """Handles vector storage and retrieval using Qdrant."""
    
    def __init__(self, url: str = None , api_key: str = None , collection_name: str = None):
        """
        Initialize the vector store.
        
        Args:
            url (str, optional): Qdrant URL. Defaults to Config.QDRANT_URL.
        """
        self.url = url or Config.QDRANT_URL
        self.api_key = api_key or Config.QDRANT_API_KEY
        self.client = QdrantClient(self.url,api_key=self.api_key)
        self.collection_name = collection_name or Config.COLLECTION_NAME
        logger.info(f"Initialized VectorStore with URL: {self.url} ,collection: {self.collection_name}")
    
    def create_collection(self, embedding_dim: int):
        """
        Create a collection in Qdrant.
        
        Args:
            embedding_dim (int): Dimension of the embedding vectors
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            logger.info(f"Creating collection '{self.collection_name}' with dimension {embedding_dim}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_dim,
                    distance=models.Distance.COSINE
                )
            )
            logger.info("Collection created successfully")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def add_documents(self, text_chunks: List[str], embeddings: List[List[float]], metas: List[dict] = None ):
        """
        Add documents to the vector store.
        
        Args:
            text_chunks (List[str]): List of text chunks
            embeddings (List[List[float]]): List of embedding vectors
        """
        try:
            if len(text_chunks) != len(embeddings):
                raise ValueError("Number of text chunks must match number of embeddings")
            
            if metas and len(metas) != len(embeddings):
                raise ValueError("Number of meta entries must match number of embeddings")
            
            if embeddings:
                self.create_collection(len(embeddings[0]))
            
            logger.info(f"Adding {len(text_chunks)} documents to collection")
            points = []
            for i, (text_chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                payload = {"text": text_chunk}
                if metas:
                    payload.update(metas[i])  # Add metadata to payload
                
                points.append(models.PointStruct(
                    id=i,
                    vector=embedding,
                    payload=payload
                ))
            self.client.upload_points(
                collection_name=self.collection_name,
                points=points
            )
            logger.info("Documents added successfully")

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(self, query_vector: List[float], limit: int = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_vector (List[float]): Query embedding vector
            limit (int, optional): Number of results to return. Defaults to Config.RETRIEVAL_LIMIT.
            
        Returns:
            List[Dict[str, Any]]: Search results with text and scores
        """
        try:
            limit = limit or Config.RETRIEVAL_LIMIT
            logger.info(f"Searching for {limit} similar documents")
            
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit
            )
            
            results = []
            for hit in search_results.points:
                results.append({
                    "text": hit.payload["text"],
                    "score": hit.score,
                    "id": hit.id
                })
            
            logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        
        Returns:
            Dict[str, Any]: Collection information
        """
        try:
            info = self.client.get_collection(self.collection_name)
            # Get points count from status
            points_count = None
            if hasattr(info, 'status') and hasattr(info.status, 'points_count'):
                points_count = info.status.points_count
            return {
                "name": self.collection_name,
                "vectors_count": points_count,
                "status": str(getattr(info, 'status', 'unknown'))
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise
    
    def delete_collection(self):
        """Delete the collection."""
        try:
            logger.info(f"Deleting collection '{self.collection_name}'")
            self.client.delete_collection(self.collection_name)
            logger.info("Collection deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    def search_with_filter(self, query_vector, limit, filters: dict):
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        query_filter = Filter(must=[FieldCondition(key=k, match=MatchValue(value=v)) for k,v in filters.items()])
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        return [
            {"id": hit.id, "score": hit.score, "text": hit.payload.get("text", ""), "metadata": hit.payload}
            for hit in results.points
        ]
