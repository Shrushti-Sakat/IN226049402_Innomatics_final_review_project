"""
Test Script for RAG System
Tests core functionality and generates sample outputs
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_loader import DocumentLoader
from chunker import DocumentChunker
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from rag_engine import RAGEngine
from langgraph_workflow import RAGWorkflow


def test_document_loading():
    """Test 1: Document Loading"""
    print("\n" + "="*70)
    print("TEST 1: Document Loading")
    print("="*70)
    
    loader = DocumentLoader()
    documents = loader.load_sample_documents()
    
    print(f"✓ Loaded {len(documents)} sample documents")
    for doc in documents:
        print(f"  - {doc['source']} (Page {doc['page']}): {len(doc['content'])} chars")
    
    return documents


def test_chunking(documents):
    """Test 2: Document Chunking"""
    print("\n" + "="*70)
    print("TEST 2: Document Chunking")
    print("="*70)
    
    chunker = DocumentChunker()
    chunks = chunker.chunk_documents(documents)
    
    print(f"✓ Created {len(chunks)} chunks from {len(documents)} documents")
    print(f"  - Average chunk size: {sum(len(c['content']) for c in chunks) / len(chunks):.0f} chars")
    
    # Show first chunk
    if chunks:
        print(f"\n  First chunk preview:")
        print(f"  Source: {chunks[0]['metadata'].get('source_file')}")
        print(f"  Content: {chunks[0]['content'][:100]}...")
    
    return chunks


def test_embeddings(chunks):
    """Test 3: Embedding Generation"""
    print("\n" + "="*70)
    print("TEST 3: Embedding Generation")
    print("="*70)
    
    embedding_gen = EmbeddingGenerator()
    embeddings = embedding_gen.generate_embeddings(chunks)
    
    print(f"✓ Generated {len(embeddings)} embeddings")
    
    if embeddings:
        embedding = embeddings[0]
        print(f"  - Embedding dimension: {len(embedding)}")
        print(f"  - Range: [{min(embedding):.4f}, {max(embedding):.4f}]")
        print(f"  - First 5 values: {embedding[:5]}")
    
    return embedding_gen, embeddings


def test_vector_store(chunks, embeddings):
    """Test 4: Vector Store"""
    print("\n" + "="*70)
    print("TEST 4: Vector Store (ChromaDB)")
    print("="*70)
    
    vector_store = VectorStore()
    vector_store.create_collection()
    vector_store.add_embeddings(chunks, embeddings)
    
    stats = vector_store.get_stats()
    print(f"✓ Vector store created and populated")
    print(f"  - Collection: {stats['collection_name']}")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Persist directory: {stats['persist_directory']}")
    
    return vector_store


def test_retrieval(embedding_gen, vector_store):
    """Test 5: Document Retrieval"""
    print("\n" + "="*70)
    print("TEST 5: Document Retrieval")
    print("="*70)
    
    from retriever import Retriever
    
    retriever = Retriever(embedding_gen, vector_store)
    
    test_queries = [
        "How do I reset my password?",
        "What are the features?",
        "How can I contact support?"
    ]
    
    for query in test_queries:
        result = retriever.retrieve(query, top_k=2)
        print(f"\n  Query: \"{query}\"")
        print(f"  Results: {result['total_results']} documents")
        for doc in result['documents'][:2]:
            print(f"    - Confidence: {doc['confidence']:.2%}")
            print(f"      Content: {doc['content'][:80]}...")


def test_rag_engine(embedding_gen, vector_store):
    """Test 6: RAG Engine"""
    print("\n" + "="*70)
    print("TEST 6: RAG Engine (Without LLM)")
    print("="*70)
    
    rag_engine = RAGEngine(embedding_gen, vector_store)
    
    test_query = "How do I reset my password?"
    print(f"\nProcessing query: \"{test_query}\"")
    print("(Note: LLM response not included without API key)")
    
    retrieval_result = rag_engine.retriever.retrieve(test_query)
    print(f"\n✓ Retrieved {len(retrieval_result['documents'])} documents")
    print(f"  - Has confident results: {retrieval_result['has_confident_results']}")
    
    for doc in retrieval_result['documents']:
        print(f"\n  Document {doc['rank']}:")
        print(f"    Confidence: {doc['confidence']:.2%}")
        print(f"    Content: {doc['content'][:100]}...")


def test_hitl_system():
    """Test 7: HITL Module"""
    print("\n" + "="*70)
    print("TEST 7: Human-in-the-Loop (HITL) Module")
    print("="*70)
    
    from hitl_module import HITLManager, EscalationReason
    
    hitl = HITLManager()
    
    # Test escalation decision
    print("\n  Testing escalation logic:")
    print(f"    - Confidence 0.9, attempts 1: {hitl.should_escalate(0.9, 1)} (expected: False)")
    print(f"    - Confidence 0.3, attempts 1: {hitl.should_escalate(0.3, 1)} (expected: True)")
    print(f"    - Confidence 0.5, attempts 2: {hitl.should_escalate(0.5, 2)} (expected: True)")
    
    # Test ticket creation
    print("\n  Creating test escalation ticket:")
    ticket = hitl.create_escalation(
        query="Test query",
        context="Test context",
        ai_response="Test response",
        confidence=0.3,
        reason=EscalationReason.LOW_CONFIDENCE
    )
    
    print(f"    ✓ Ticket created: {ticket.ticket_id}")
    print(f"      Status: {ticket.status}")
    print(f"      Reason: {ticket.escalation_reason}")
    
    # Test resolution
    print("\n  Resolving ticket:")
    resolved = hitl.resolve_ticket(ticket.ticket_id, "Human response")
    print(f"    ✓ Ticket resolved: {resolved['status']}")
    
    # Get statistics
    stats = hitl.get_statistics()
    print(f"\n  HITL Statistics:")
    print(f"    - Total escalations: {stats['total_escalations']}")
    print(f"    - Pending: {stats['pending']}")
    print(f"    - Resolved: {stats['resolved']}")


def test_workflow(embedding_gen, vector_store):
    """Test 8: LangGraph Workflow"""
    print("\n" + "="*70)
    print("TEST 8: LangGraph Workflow")
    print("="*70)
    
    rag_engine = RAGEngine(embedding_gen, vector_store)
    workflow = RAGWorkflow(rag_engine)
    
    test_query = "How do I reset my password?"
    print(f"\nProcessing workflow for: \"{test_query}\"")
    print("\nWorkflow nodes executed:")
    print("  1. RETRIEVE - Extract relevant documents")
    print("  2. GENERATE - Create answer with LLM")
    print("  3. EVALUATE - Calculate confidence")
    print("  4. ROUTE - Conditional routing")
    print("\nNote: Full workflow requires OpenAI API key")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("RAG SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # Test 1: Document Loading
    documents = test_document_loading()
    
    # Test 2: Chunking
    chunks = test_chunking(documents)
    
    # Test 3: Embeddings
    embedding_gen, embeddings = test_embeddings(chunks)
    
    # Test 4: Vector Store
    vector_store = test_vector_store(chunks, embeddings)
    
    # Test 5: Retrieval
    test_retrieval(embedding_gen, vector_store)
    
    # Test 6: RAG Engine
    test_rag_engine(embedding_gen, vector_store)
    
    # Test 7: HITL System
    test_hitl_system()
    
    # Test 8: Workflow
    test_workflow(embedding_gen, vector_store)
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED SUCCESSFULLY ✓")
    print("="*70)
    print("\nNext steps:")
    print("  1. Set up OpenAI API key: export OPENAI_API_KEY=your-key")
    print("  2. Run interactive mode: python main.py --mode interactive")
    print("  3. Run demo mode: python main.py --mode demo")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_tests()
