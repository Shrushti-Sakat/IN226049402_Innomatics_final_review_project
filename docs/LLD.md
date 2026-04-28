# Low-Level Design (LLD)
## RAG-Based Customer Support Assistant with LangGraph & HITL

---

## Table of Contents
1. Module-Level Design
2. Data Structures
3. Workflow Design (LangGraph Implementation)
4. Conditional Routing Logic
5. HITL Design Details
6. API/Interface Design
7. Error Handling Strategy
8. Performance Metrics
9. Database Schema

---

## 1. Module-Level Design

### 1.1 Document Processing Module (`document_loader.py`)

**Class**: `DocumentLoader`

**Attributes**:
```python
- data_dir: Path          # Directory containing PDFs
- documents: List[Dict]   # Loaded documents
```

**Methods**:
```python
load_pdfs() -> List[Dict]
    """Load all PDFs from data directory"""
    Returns: List of dicts with keys:
    - content: str (document text)
    - source: str (filename)
    - page: int (page number)
    - metadata: Dict

_load_single_pdf(pdf_path: Path) -> None
    """Load a single PDF file"""

load_sample_documents() -> List[Dict]
    """Generate sample documents for testing"""
```

**Data Flow**:
```
Input: PDF Files → Read with PyPDF2 → Extract Text → Store in memory
```

---

### 1.2 Chunking Module (`chunker.py`)

**Class**: `DocumentChunker`

**Attributes**:
```python
- chunk_size: int        # Characters per chunk (default: 500)
- chunk_overlap: int     # Overlap size (default: 100)
```

**Methods**:
```python
chunk_documents(documents: List[Dict]) -> List[Dict]
    """Break documents into chunks"""
    Input: documents from DocumentLoader
    Output: List of chunk dicts with:
    - content: str
    - metadata: Dict
    - chunk_index: int
    - total_chunks: int

_chunk_text(text: str, metadata: Dict) -> List[Dict]
    """Split single document text into overlapping chunks"""
```

**Chunking Algorithm**:
```
if len(text) <= chunk_size:
    return [text]
else:
    step = chunk_size - chunk_overlap
    chunks = []
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        chunks.append({
            "content": chunk,
            "metadata": metadata,
            "chunk_index": len(chunks),
            "start_char": i,
            "end_char": i + chunk_size
        })
    return chunks
```

**Example**:
```
Text: "ABCDEFGHIJ..." (1000 chars)
Chunk Size: 500, Overlap: 100

Chunk 1: 0-500 (A-U)
Chunk 2: 400-900 (Q-Y)
Chunk 3: 800-1000 (W-Z)
```

---

### 1.3 Embedding Module (`embeddings.py`)

**Class**: `EmbeddingGenerator`

**Attributes**:
```python
- model_name: str                    # Model ID
- model: SentenceTransformer         # Loaded model
```

**Methods**:
```python
generate_embeddings(chunks: List[Dict]) -> List[List[float]]
    """Generate embeddings for multiple chunks"""
    Input: List of chunks
    Output: List of embedding vectors (N × 384)
    Process: Batch encoding with progress bar

generate_query_embedding(query: str) -> List[float]
    """Generate embedding for a single query"""
    Input: Query string
    Output: Single embedding vector (384,)
```

**Model Specifications**:
```
Model: all-MiniLM-L6-v2
Architecture: Transformer (6 layers)
Embedding Dimension: 384
Max Sequence Length: 512 tokens
Training Data: SNLI, MultiNLI, AllNLI
Parameters: 22.7M
Size: 33 MB
```

**Embedding Properties**:
- Type: Dense vector
- Dimension: 384
- Range: [-1, 1] (normalized)
- Similarity: Cosine similarity

---

### 1.4 Vector Storage Module (`vector_store.py`)

**Class**: `VectorStore`

**Attributes**:
```python
- persist_dir: str          # Directory for ChromaDB
- client: chromadb.Client   # ChromaDB client
- collection: Collection    # Active collection
```

**Methods**:
```python
create_collection(name: str) -> None
    """Create or get ChromaDB collection"""

add_embeddings(chunks: List[Dict], 
               embeddings: List[List[float]]) -> None
    """Add embeddings to vector store"""
    Process:
    - Generate unique IDs: chunk_{i}
    - Prepare metadata
    - Batch insert into ChromaDB

query(query_embedding: List[float], top_k: int) -> Dict
    """Query vector store"""
    Input: Query embedding, K
    Output: {
        "ids": List[str],
        "documents": List[str],
        "metadatas": List[Dict],
        "distances": List[float]
    }

get_stats() -> Dict
    """Return collection statistics"""
```

**ChromaDB Configuration**:
```python
Collection Name: "customer_support_docs"
Persist Directory: "./chroma_db"
Metric: "cosine"  # Distance metric
HNSW Space: "cosine"  # Index configuration
```

---

### 1.5 Retriever Module (`retriever.py`)

**Class**: `Retriever`

**Attributes**:
```python
- embedding_gen: EmbeddingGenerator
- vector_store: VectorStore
```

**Methods**:
```python
retrieve(query: str, top_k: int) -> Dict
    """Retrieve relevant documents"""
    Steps:
    1. Generate query embedding
    2. Search vector store
    3. Convert distances to confidence scores
    4. Return ranked results
    
    Output: {
        "query": str,
        "documents": [
            {
                "id": str,
                "content": str,
                "metadata": Dict,
                "confidence": float [0, 1],
                "rank": int
            }
        ],
        "total_results": int,
        "has_confident_results": bool
    }

format_context(retrieval_result: Dict) -> str
    """Format retrieved documents as context string"""
    Output: Formatted string with sources and confidence
```

**Confidence Calculation**:
```
confidence = 1 - (cosine_distance / 2)
confidence = clamp(confidence, 0, 1)
```

---

### 1.6 RAG Engine Module (`rag_engine.py`)

**Class**: `RAGEngine`

**Attributes**:
```python
- embedding_gen: EmbeddingGenerator
- vector_store: VectorStore
- retriever: Retriever
- hitl_manager: HITLManager
- attempt_count: Dict[str, int]
```

**Methods**:
```python
process_query(query: str, enable_hitl: bool) -> Dict
    """End-to-end query processing"""
    Process:
    1. Retrieve documents
    2. Generate answer with LLM
    3. Calculate confidence
    4. Determine escalation
    
    Output: Response with metadata

_generate_answer(query: str, context: str) -> Dict
    """Generate answer using LLM"""
    Uses: OpenAI GPT-3.5-turbo
    
_calculate_confidence(retrieval_result: Dict, 
                      llm_response: Dict) -> float
    """Calculate confidence score"""
    Factors:
    - Retrieval confidence
    - Document count
    - Uncertainty phrases in response

_determine_escalation_reason() -> EscalationReason
    """Determine why escalation is needed"""
```

**LLM Configuration**:
```
Model: gpt-3.5-turbo
Temperature: 0.7
Max Tokens: 500
Timeout: 30 seconds
```

---

### 1.7 HITL Module (`hitl_module.py`)

**Classes**: `HITLManager`, `EscalationTicket`, `EscalationReason`

**EscalationReason (Enum)**:
```python
- LOW_CONFIDENCE: confidence < 0.4
- NO_CONTEXT: no relevant documents found
- COMPLEX_QUERY: multiple attempts needed
- MULTIPLE_ATTEMPTS: max attempts reached
- USER_REQUEST: user explicitly asked
```

**EscalationTicket (Dataclass)**:
```python
@dataclass
class EscalationTicket:
    ticket_id: str              # Unique ID
    query: str                  # Original query
    retrieved_context: str      # Retrieved documents
    ai_response: str           # AI attempted answer
    ai_confidence: float       # Confidence score
    escalation_reason: str     # Reason for escalation
    timestamp: str             # ISO 8601 timestamp
    status: str                # pending/resolved/closed
    human_response: Optional[str]  # Human's response
```

**HITLManager Methods**:
```python
should_escalate(confidence: float, attempt_count: int) -> bool
    """Determine if escalation needed"""
    Logic:
    if confidence < 0.4: return True
    if attempt_count >= 2: return True
    return False

create_escalation_ticket() -> EscalationTicket
    """Create new escalation ticket"""
    
resolve_ticket(ticket_id: str, human_response: str) -> Dict
    """Resolve escalation with human response"""
    
get_pending_tickets() -> List[Dict]
    """Get unresolved tickets"""
    
get_statistics() -> Dict
    """Return escalation statistics"""
```

---

### 1.8 LangGraph Workflow Module (`langgraph_workflow.py`)

**Class**: `RAGWorkflow`

**State Object** (`GraphState`):
```python
@dataclass
class GraphState:
    query: str                      # User query
    retrieved_context: Optional[str]  # Retrieved docs
    ai_response: Optional[str]      # Generated answer
    confidence: float = 0.0         # Confidence score
    should_escalate: bool = False   # Escalation flag
    final_response: Optional[str]   # Final output
    metadata: Dict = None           # Additional data
```

**Workflow Nodes**:

```
Node 1: _node_retrieve()
├─ Input: GraphState with query
├─ Process:
│  1. Call retriever.retrieve()
│  2. Format context
│  3. Store retrieved documents count
└─ Output: Updated state with retrieved_context

Node 2: _node_generate_answer()
├─ Input: GraphState with context
├─ Process:
│  1. Call RAG engine LLM generation
│  2. Handle errors
│  3. Store model info
└─ Output: Updated state with ai_response

Node 3: _node_evaluate_and_route()
├─ Input: GraphState with response
├─ Process:
│  1. Calculate confidence
│  2. Check escalation criteria
│  3. Determine routing
└─ Output: Updated state with confidence & should_escalate

Node 4a: _node_escalate()
├─ Condition: should_escalate == True
├─ Process:
│  1. Create HITL ticket
│  2. Store ticket ID
│  3. Format escalation response
└─ Output: Updated state with final_response & ticket_id

Node 4b: _node_respond()
├─ Condition: should_escalate == False
├─ Process:
│  1. Set final response to AI response
│  2. Mark as direct response
└─ Output: Updated state with final_response
```

**Workflow Execution**:
```python
def process_query_workflow(query: str) -> Dict:
    state = GraphState(query=query)
    state = _node_retrieve(state)           # Step 1
    state = _node_generate_answer(state)    # Step 2
    state = _node_evaluate_and_route(state) # Step 3
    
    if state.should_escalate:
        state = _node_escalate(state)       # Step 4a
    else:
        state = _node_respond(state)        # Step 4b
    
    return format_output(state)
```

---

## 2. Data Structures

### 2.1 Document Structure
```python
Document = {
    "content": str,              # Full document text
    "source": str,              # Filename
    "page": int,                # Page number
    "metadata": {
        "source_file": str,
        "page_number": int,
        "total_pages": int
    }
}
```

### 2.2 Chunk Structure
```python
Chunk = {
    "content": str,             # 500 character snippet
    "metadata": Dict,           # Inherited from document
    "chunk_index": int,         # Position in document
    "total_chunks": int,        # Total chunks in document
    "start_char": int,          # Starting position in original
    "end_char": int             # Ending position in original
}
```

### 2.3 Embedding Structure
```python
Embedding = List[float]    # 384-dimensional vector
                           # Range: [-1, 1]
                           # Type: float32
```

### 2.4 Retrieval Result Structure
```python
RetrievalResult = {
    "query": str,
    "documents": [
        {
            "id": str,           # chunk_0, chunk_1, etc.
            "content": str,      # Chunk text
            "metadata": Dict,    # Source info
            "confidence": float, # [0, 1]
            "rank": int          # 1, 2, 3...
        }
    ],
    "total_results": int,
    "has_confident_results": bool
}
```

### 2.5 LLM Response Structure
```python
LLMResponse = {
    "answer": str,              # Generated response
    "model": str,              # gpt-3.5-turbo or error
    "tokens_used": int,        # Token count
    "error": Optional[str]     # Error message if any
}
```

### 2.6 Query Processing Output
```python
QueryOutput = {
    "status": str,             # success/escalated/error
    "query": str,              # Original query
    "answer": str,             # Response to user
    "confidence": float,       # [0, 1]
    "sources": List[str],      # Document sources
    "context_used": int,       # Number of chunks
    "ticket_id": Optional[str], # If escalated
    "metadata": Dict           # Additional info
}
```

---

## 3. Workflow Design (LangGraph Implementation)

### 3.1 Graph Structure

```
┌─────────────────────────────┐
│      START: Query Input     │
└──────────────┬──────────────┘
               │
               ▼
        ┌─────────────────┐
        │ Node 1: RETRIEVE│
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Node 2: GENERATE│
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Node 3: EVALUATE│
        └────────┬────────┘
                 │
         ┌───────┴────────┐
         │                │
    confidence     confidence
      >= 0.4        < 0.4
         │                │
         ▼                ▼
    ┌────────┐      ┌──────────┐
    │ RESPOND│      │ ESCALATE │
    └───┬────┘      └────┬─────┘
        │                │
        └────────┬───────┘
                 │
                 ▼
        ┌─────────────────┐
        │ END: Return     │
        │ Response        │
        └─────────────────┘
```

### 3.2 State Transitions

```
RETRIEVE Node:
- Input: GraphState(query=Q)
- Output: GraphState(query=Q, retrieved_context=C)
- Data Added: retrieved_context, retrieval_count, retrieval_result

GENERATE Node:
- Input: GraphState(retrieved_context=C)
- Output: GraphState(ai_response=A)
- Data Added: ai_response, model info, tokens

EVALUATE Node:
- Input: GraphState(ai_response=A)
- Output: GraphState(confidence=F, should_escalate=B)
- Calculation: Confidence based on retrieval & response quality

ROUTING Decision:
- If should_escalate=True: → ESCALATE Node
- Else: → RESPOND Node

ESCALATE Node:
- Input: All previous data
- Output: final_response="Escalated, Ticket: X"
- Action: Create HITL ticket, notify human

RESPOND Node:
- Input: ai_response=A
- Output: final_response=A
- Action: Prepare response for user
```

---

## 4. Conditional Routing Logic

### 4.1 Escalation Conditions

```python
def should_escalate(confidence: float, attempt_count: int) -> bool:
    """
    Determine if escalation is needed
    
    Conditions (OR logic):
    1. confidence < ESCALATION_THRESHOLD (0.4)
    2. attempt_count >= MAX_ATTEMPTS (2)
    3. No relevant context found
    """
    
    conditions = {
        "low_confidence": confidence < 0.4,
        "max_attempts": attempt_count >= 2,
        "no_context": not has_context,
    }
    
    return any(conditions.values())
```

### 4.2 Confidence Calculation

```python
def calculate_confidence(retrieval_result, llm_response) -> float:
    """
    Confidence = Base * Adjustments
    
    Base: Average confidence from top-3 retrieval results
    Adjustments:
    - If no documents: 0.0
    - If uncertainty phrases found: × 0.6
    - Cap at 1.0
    """
    
    if not retrieval_result["documents"]:
        return 0.0
    
    avg_conf = mean([doc["confidence"] 
                     for doc in retrieval_result["documents"]])
    
    if has_uncertainty_phrases(llm_response):
        avg_conf *= 0.6
    
    return min(1.0, avg_conf)
```

### 4.3 Answer Generation Criteria

```
Generate Direct Answer if:
✓ Confidence >= 0.4
✓ Retrieved at least 1 relevant document
✓ First or second attempt
✓ Response doesn't contain uncertainty phrases

Escalate if:
✗ Confidence < 0.4
✗ No relevant documents found
✗ Multiple attempts failed
✗ Complex query indicators present
```

---

## 5. HITL Design Details

### 5.1 Escalation Ticket Lifecycle

```
1. CREATION
   - ticket_id: ESCALATION-00001
   - status: "pending"
   - timestamp: ISO 8601
   - Store all context

2. PENDING
   - Ticket visible to human agents
   - AI response and context provided
   - Confidence score shown
   - Escalation reason displayed

3. RESOLUTION
   - Human provides response
   - Response stored in ticket
   - status: "resolved"
   - Resolution timestamp added

4. CLOSURE
   - Ticket archived
   - Statistics updated
   - Feedback collected (optional)
```

### 5.2 Ticket Storage

```python
tickets: Dict[str, EscalationTicket] = {}

# Access pattern:
ticket = tickets["ESCALATION-00001"]

# Query patterns:
pending = [t for t in tickets.values() 
           if t.status == "pending"]
resolved = [t for t in tickets.values() 
            if t.status == "resolved"]
```

### 5.3 Statistics Tracking

```python
Statistics = {
    "total_escalations": int,
    "pending": int,
    "resolved": int,
    "closed": int,
    "escalation_rate": float,  # % of total queries
    "avg_resolution_time": float,  # seconds
}
```

---

## 6. API/Interface Design

### 6.1 Input Interface

**CLI Input Format**:
```
$ python main.py --mode interactive
💬 Enter your question: How do I reset my password?

$ python main.py --mode test --query "What is your product?"

$ python main.py --mode demo
```

**Programmatic Input**:
```python
from main import RAGAssistant

assistant = RAGAssistant(use_sample_data=True)
result = assistant.process_query("Your question here?")
```

### 6.2 Output Format

**Success Response**:
```json
{
    "status": "success",
    "query": "How do I reset my password?",
    "answer": "To reset your password, follow these steps...",
    "confidence": 0.85,
    "sources": ["troubleshooting.pdf", "support_guide.pdf"],
    "context_used": 3,
    "model": "gpt-3.5-turbo"
}
```

**Escalated Response**:
```json
{
    "status": "escalated",
    "query": "How do I reset my password?",
    "answer": "Your query has been escalated to our support team. Ticket ID: ESCALATION-00001",
    "ticket_id": "ESCALATION-00001",
    "confidence": 0.35,
    "ai_response": "[Attempted answer]",
    "reasoning": "Low confidence in automatic answer"
}
```

**Error Response**:
```json
{
    "status": "error",
    "query": "Your question",
    "error": "Error message",
    "message": "Unable to process query at this time"
}
```

---

## 7. Error Handling Strategy

### 7.1 Error Types and Handling

```python
class DocumentLoadError:
    """Handle PDF loading failures"""
    Strategy: Skip file, log error, continue with next

class ChunkingError:
    """Handle chunking failures"""
    Strategy: Return fallback chunks, log error

class EmbeddingError:
    """Handle embedding generation failures"""
    Strategy: Fallback to simple string matching, alert user

class VectorStoreError:
    """Handle ChromaDB failures"""
    Strategy: Retry operation, use cache if available

class LLMError:
    """Handle OpenAI API failures"""
    Strategy: Return generic response, mark for escalation

class RetrievalError:
    """Handle empty retrieval results"""
    Strategy: Escalate to human automatically
```

### 7.2 Error Recovery

```
Level 1 (Retry):
- Transient errors (timeout, rate limit)
- Action: Retry up to 3 times with backoff

Level 2 (Fallback):
- Missing embeddings
- Action: Use simple TF-IDF retrieval

Level 3 (Escalate):
- Critical failures
- Action: Create HITL ticket, notify user
```

---

## 8. Performance Metrics

### 8.1 Operation Latencies

```
Component                   Latency         Notes
──────────────────────────────────────────────────
Query Embedding             ~50ms          Batch processing
Vector Search               ~20ms          Cosine similarity
Context Formatting          ~10ms          String operations
LLM Inference              ~2-3s          OpenAI API call
Confidence Calculation      ~5ms           Simple math
HITL Ticket Creation       ~20ms          Database write
──────────────────────────────────────────────────
Total (Success Path)       ~3-4s          End-to-end
Total (Escalated Path)     ~3.5-4.5s      + ticket overhead
```

### 8.2 Throughput

```
Single Instance:
- Queries/second: ~0.25-0.3 (limited by LLM)
- Max concurrent: 5-10 (OpenAI rate limits)
- Queries/hour: ~1000-1500

With Caching:
- Hit rate: ~30-40% (typical)
- Effective QPS: ~0.4-0.5
```

### 8.3 Resource Usage

```
Memory:
- Python Process: ~500 MB
- Embedding Model: ~100 MB
- Vector Store (5000 docs): ~50 MB
- Total: ~650 MB

Disk:
- Embedding Model: 33 MB
- ChromaDB: ~50 MB (scales linearly)
- Logs: ~1 MB/1000 queries
```

---

## 9. Database Schema

### 9.1 ChromaDB Collection Schema

```python
Collection: "customer_support_docs"

Document Structure:
├─ id: str               # Unique ID (chunk_0, chunk_1, ...)
├─ embedding: List[float] # 384-dim vector
├─ document: str         # Chunk content (indexed)
├─ metadata: Dict
│  ├─ source_file: str   # Original PDF
│  ├─ page_number: int   # Page in PDF
│  ├─ chunk_index: int   # Position in document
│  └─ total_chunks: int  # Total chunks in document
└─ created_at: datetime  # Insertion timestamp
```

### 9.2 HITL Ticket Schema

```python
tickets: Dict[str, EscalationTicket]

EscalationTicket fields:
├─ ticket_id: str                  # ESCALATION-00001
├─ query: str                      # Original question
├─ retrieved_context: str          # Retrieved docs
├─ ai_response: str               # AI attempted answer
├─ ai_confidence: float           # Confidence [0, 1]
├─ escalation_reason: str         # low_confidence, etc.
├─ timestamp: str                 # ISO 8601
├─ status: str                    # pending/resolved/closed
├─ human_response: Optional[str]  # Human's reply
└─ resolution_timestamp: Optional[str]
```

---

## 10. Configuration Parameters

```python
# Chunking
CHUNK_SIZE = 500              # Characters per chunk
CHUNK_OVERLAP = 100           # Overlap size

# Retrieval
TOP_K_RESULTS = 3             # Top results to retrieve
CONFIDENCE_THRESHOLD = 0.5    # For display purposes

# LLM
LLM_TEMPERATURE = 0.7         # Creativity parameter
LLM_MAX_TOKENS = 500          # Response length limit

# HITL
ESCALATION_THRESHOLD = 0.4    # When to escalate
MAX_ATTEMPTS = 2              # Before escalation

# Embedding
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Vector Store
CHROMA_COLLECTION_NAME = "customer_support_docs"
CHROMA_PERSIST_DIRECTORY = "./chroma_db"
```

---

**Document Version**: 1.0
**Date**: 2024
**Status**: LLD Complete
