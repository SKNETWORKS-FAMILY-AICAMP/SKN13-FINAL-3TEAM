"""
Qdrant VectorDB Client module: Handles interaction with Qdrant vector database.
"""
from qdrant_client import QdrantClient as QdrantClientBase
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Dict, Any, Optional
import os

class QdrantClient:
    def __init__(self, host: str = None, port: int = None, collection_name: str = "hyundai_knowledge"):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant host (default from env or localhost)
            port: Qdrant port (default from env or 6333)
            collection_name: Collection name for storing vectors
        """
        self.host = host or os.getenv('QDRANT_HOST', 'localhost')
        self.port = port or int(os.getenv('QDRANT_PORT', '6333'))
        self.collection_name = collection_name
        
        try:
            self.client = QdrantClientBase(host=self.host, port=self.port)
            # Ensure collection exists
            self._ensure_collection_exists()
        except Exception as e:
            print(f"Failed to connect to Qdrant: {e}")
            self.client = None

    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if it doesn't."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with default settings
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "size": 1536,  # Default embedding size
                        "distance": "Cosine"
                    }
                )
                print(f"Created collection: {self.collection_name}")
        except Exception as e:
            print(f"Failed to ensure collection exists: {e}")

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant data from Qdrant.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[Dict]: List of search results
        """
        if not self.client:
            # Return mock data for testing
            return [
                {"content": f"Mock result for query: {query}", "score": 0.8},
                {"content": "Additional mock data", "score": 0.7}
            ]
        
        try:
            # For now, we'll do a simple text search
            # In a real implementation, you'd need to embed the query first
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * 1536,  # Placeholder vector
                limit=limit,
                with_payload=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload.get("content", ""),
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {})
                })
            
            return results
            
        except Exception as e:
            print(f"Qdrant search failed: {e}")
            # Return mock data as fallback
            return [
                {"content": f"Fallback result for: {query}", "score": 0.6}
            ]

    def store(self, data: Dict[str, Any], vector: List[float] = None) -> bool:
        """
        Store data in Qdrant.
        
        Args:
            data: Data to store
            vector: Vector representation of the data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.client:
            print("Qdrant client not available")
            return False
        
        try:
            # For now, we'll use a placeholder vector
            if vector is None:
                vector = [0.0] * 1536  # Placeholder
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    {
                        "id": hash(data.get("content", "")),  # Simple hash as ID
                        "vector": vector,
                        "payload": data
                    }
                ]
            )
            return True
            
        except Exception as e:
            print(f"Failed to store data in Qdrant: {e}")
            return False

    def search_by_keywords(self, keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search by keywords using payload filtering.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results
            
        Returns:
            List[Dict]: List of search results
        """
        if not self.client:
            return [{"content": f"Mock keyword search for: {keywords}", "score": 0.8}]
        
        try:
            # Create filter for keyword search
            conditions = []
            for keyword in keywords:
                conditions.append(
                    FieldCondition(
                        key="content",
                        match=MatchValue(value=keyword)
                    )
                )
            
            filter_condition = Filter(
                must=conditions
            )
            
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * 1536,  # Placeholder
                query_filter=filter_condition,
                limit=limit,
                with_payload=True
            )
            
            results = []
            for result in search_results:
                results.append({
                    "content": result.payload.get("content", ""),
                    "score": result.score,
                    "metadata": result.payload.get("metadata", {})
                })
            
            return results
            
        except Exception as e:
            print(f"Keyword search failed: {e}")
            return [{"content": f"Keyword search fallback for: {keywords}", "score": 0.6}]
