"""
Chunking Module
Breaks down documents into manageable chunks for embedding
"""

from typing import List, Dict
from config import CHUNK_SIZE, CHUNK_OVERLAP


class DocumentChunker:
    """Split documents into overlapping chunks"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        """
        Initialize DocumentChunker
        
        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Break documents into chunks
        
        Args:
            documents: List of documents with content
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        for doc in documents:
            doc_chunks = self._chunk_text(
                doc["content"],
                doc.get("metadata", {})
            )
            chunks.extend(doc_chunks)
        
        print(f"Created {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            metadata: Document metadata
            
        Returns:
            List of chunks
        """
        chunks = []
        
        # Clean and normalize text
        text = text.strip()
        
        if len(text) <= self.chunk_size:
            # If text is smaller than chunk size, return as single chunk
            chunks.append({
                "content": text,
                "metadata": metadata,
                "chunk_index": 0,
                "total_chunks": 1
            })
            return chunks
        
        # Create overlapping chunks
        step = self.chunk_size - self.chunk_overlap
        chunk_index = 0
        
        for i in range(0, len(text), step):
            chunk = text[i:i + self.chunk_size]
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append({
                    "content": chunk,
                    "metadata": metadata,
                    "chunk_index": chunk_index,
                    "start_char": i,
                    "end_char": min(i + self.chunk_size, len(text))
                })
                chunk_index += 1
            
            # Don't create partial chunks at the end
            if i + self.chunk_size >= len(text):
                break
        
        # Add total chunk count to all chunks
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)
        
        return chunks
