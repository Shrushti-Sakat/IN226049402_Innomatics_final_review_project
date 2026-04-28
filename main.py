"""
Main Module
Entry point for the RAG Customer Support Assistant
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from document_loader import DocumentLoader
from chunker import DocumentChunker
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from rag_engine import RAGEngine
from langgraph_workflow import RAGWorkflow


class RAGAssistant:
    """Main RAG Assistant class"""
    
    def __init__(self, use_sample_data: bool = True):
        """
        Initialize RAG Assistant
        
        Args:
            use_sample_data: Whether to use sample data for demo
        """
        print("=" * 60)
        print("Initializing RAG Customer Support Assistant")
        print("=" * 60)
        
        # Initialize components
        print("\n[1/5] Initializing embeddings...")
        self.embedding_gen = EmbeddingGenerator()
        
        print("[2/5] Initializing vector store...")
        self.vector_store = VectorStore()
        self.vector_store.create_collection()
        
        # Load and process documents
        print("[3/5] Loading documents...")
        loader = DocumentLoader()
        
        if use_sample_data:
            documents = loader.load_sample_documents()
            print(f"   Loaded {len(documents)} sample documents")
        else:
            documents = loader.load_pdfs()
            if not documents:
                print("   No documents found, using sample data")
                documents = loader.load_sample_documents()
        
        print("[4/5] Chunking documents...")
        chunker = DocumentChunker()
        chunks = chunker.chunk_documents(documents)
        
        print("[5/5] Generating embeddings...")
        embeddings = self.embedding_gen.generate_embeddings(chunks)
        self.vector_store.add_embeddings(chunks, embeddings)
        
        # Initialize RAG and workflow
        self.rag_engine = RAGEngine(self.embedding_gen, self.vector_store)
        self.workflow = RAGWorkflow(self.rag_engine)
        
        print("\n" + "=" * 60)
        print("System initialized successfully!")
        print("=" * 60)
        print(f"Vector Store Stats: {self.vector_store.get_stats()}")
        print("=" * 60 + "\n")
    
    def process_query(self, query: str) -> dict:
        """
        Process a customer support query
        
        Args:
            query: Customer query
            
        Returns:
            Response from the system
        """
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        result = self.workflow.process_query_workflow(query, enable_hitl=True)
        
        print(f"\n✅ Response:")
        print(result["response"])
        print(f"\nConfidence: {result['confidence']:.2%}")
        
        if result.get("escalated"):
            print(f"⚠️  Escalated to human (Ticket: {result['metadata'].get('ticket_id')})")
        
        print("-" * 60)
        
        return result
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("\n" + "=" * 60)
        print("Interactive Mode - Type 'exit' to quit")
        print("=" * 60 + "\n")
        
        while True:
            try:
                query = input("\n💬 Enter your question: ").strip()
                
                if query.lower() in ["exit", "quit", "q"]:
                    print("\nThank you for using RAG Customer Support Assistant!")
                    break
                
                if not query:
                    print("Please enter a valid question.")
                    continue
                
                self.process_query(query)
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
    
    def get_escalation_stats(self):
        """Get escalation statistics"""
        return self.rag_engine.hitl_manager.get_statistics()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Customer Support Assistant")
    parser.add_argument("--mode", choices=["interactive", "demo", "test"],
                       default="interactive",
                       help="Operation mode")
    parser.add_argument("--query", type=str, help="Single query to process")
    parser.add_argument("--no-sample", action="store_true",
                       help="Don't use sample data (load from PDF files)")
    
    args = parser.parse_args()
    
    # Initialize assistant
    assistant = RAGAssistant(use_sample_data=not args.no_sample)
    
    # Run in selected mode
    if args.mode == "interactive":
        assistant.interactive_mode()
    
    elif args.mode == "demo":
        print("\n" + "=" * 60)
        print("Running Demo Mode with Sample Queries")
        print("=" * 60)
        
        demo_queries = [
            "What is your response time for urgent issues?",
            "How do I reset my password?",
            "What are the main features of your product?",
            "How can I contact customer support?"
        ]
        
        for query in demo_queries:
            assistant.process_query(query)
        
        print("\n" + "=" * 60)
        print("Escalation Statistics:")
        print(assistant.get_escalation_stats())
        print("=" * 60)
    
    elif args.mode == "test":
        if args.query:
            assistant.process_query(args.query)
        else:
            print("Test mode requires --query argument")


if __name__ == "__main__":
    main()
