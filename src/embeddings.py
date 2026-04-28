"""
Embeddings Module
Generates embeddings using sentence-transformers
"""

from typing import List, Dict
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """
        Initialize EmbeddingGenerator
        
        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        print(f"Loaded embedding model: {model_name}")
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[List[float]]:
        """
        Generate embeddings for chunks
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of embedding vectors
        """
        texts = [chunk["content"] for chunk in chunks]
        
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        print(f"Generated {len(embeddings)} embeddings")
        return embeddings.tolist()
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            query: Query text
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode([query])
        return embedding[0].tolist()
