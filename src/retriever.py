"""
Retriever Module
Handles document retrieval based on queries
"""

from typing import List, Dict, Tuple
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from config import TOP_K_RESULTS, CONFIDENCE_THRESHOLD


class Retriever:
    """Retrieve relevant documents based on queries"""
    
    def __init__(self, embedding_gen: EmbeddingGenerator, vector_store: VectorStore):
        """
        Initialize Retriever
        
        Args:
            embedding_gen: EmbeddingGenerator instance
            vector_store: VectorStore instance
        """
        self.embedding_gen = embedding_gen
        self.vector_store = vector_store
    
    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> Dict:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query string
            top_k: Number of top results to return
            
        Returns:
            Retrieved documents with confidence scores
        """
        # Generate query embedding
        query_embedding = self.embedding_gen.generate_query_embedding(query)
        
        # Query vector store
        results = self.vector_store.query(query_embedding, top_k=top_k)
        
        # Calculate confidence scores (inverse of distance)
        # Distance in cosine similarity: 0 = identical, 2 = most different
        # Convert to confidence: 1 - (distance/2)
        documents = []
        
        for i, (doc_id, content, metadata, distance) in enumerate(zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            # Normalize cosine distance to confidence [0, 1]
            confidence = 1 - (distance / 2)
            confidence = max(0, min(1, confidence))  # Clamp to [0, 1]
            
            documents.append({
                "id": doc_id,
                "content": content,
                "metadata": metadata,
                "confidence": confidence,
                "rank": i + 1
            })
        
        return {
            "query": query,
            "documents": documents,
            "total_results": len(documents),
            "has_confident_results": any(doc["confidence"] >= CONFIDENCE_THRESHOLD for doc in documents)
        }
    
    def format_context(self, retrieval_result: Dict) -> str:
        """
        Format retrieved documents as context string
        
        Args:
            retrieval_result: Result from retrieve()
            
        Returns:
            Formatted context string
        """
        if not retrieval_result["documents"]:
            return "No relevant documents found."
        
        context_parts = []
        
        for doc in retrieval_result["documents"]:
            context_parts.append(f"[Source: {doc['metadata'].get('source_file', 'Unknown')} - Confidence: {doc['confidence']:.2%}]")
            context_parts.append(doc["content"])
            context_parts.append("")
        
        return "\n".join(context_parts)
