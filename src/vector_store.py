"""
Vector Store Module
Manages ChromaDB for storing and retrieving embeddings
"""

import chromadb
from typing import List, Dict, Optional
from config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIRECTORY


class VectorStore:
    """Wrapper for ChromaDB vector database"""
    
    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIRECTORY):
        """
        Initialize VectorStore with ChromaDB
        
        Args:
            persist_dir: Directory for ChromaDB persistence
        """
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = None
    
    def create_collection(self, collection_name: str = CHROMA_COLLECTION_NAME) -> None:
        """
        Create or get a ChromaDB collection
        
        Args:
            collection_name: Name of the collection
        """
        try:
            # Try to get existing collection
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
        except:
            # Create new collection
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection: {collection_name}")
    
    def add_embeddings(self, chunks: List[Dict], embeddings: List[List[float]]) -> None:
        """
        Add embeddings to the vector store
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
        """
        if not self.collection:
            raise ValueError("Collection not initialized. Call create_collection first.")
        
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings count mismatch")
        
        ids = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{i}"
            ids.append(chunk_id)
            documents.append(chunk["content"])
            
            metadata = chunk.get("metadata", {})
            metadata["chunk_index"] = chunk.get("chunk_index", 0)
            metadatas.append(metadata)
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Added {len(chunks)} embeddings to vector store")
    
    def query(self, query_embedding: List[float], top_k: int = 3) -> Dict:
        """
        Query the vector store
        
        Args:
            query_embedding: Embedding vector for the query
            top_k: Number of top results to return
            
        Returns:
            Query results with documents and distances
        """
        if not self.collection:
            raise ValueError("Collection not initialized")
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics
        
        Returns:
            Collection statistics
        """
        if not self.collection:
            return {"error": "Collection not initialized"}
        
        count = self.collection.count()
        return {
            "collection_name": self.collection.name,
            "total_documents": count,
            "persist_directory": self.persist_dir
        }
    
    def clear_collection(self) -> None:
        """Clear all data from the collection"""
        if self.collection:
            self.client.delete_collection(name=self.collection.name)
            self.collection = None
            print("Collection cleared")
