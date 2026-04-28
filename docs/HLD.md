# High-Level Design (HLD)
## RAG-Based Customer Support Assistant with LangGraph & HITL

---

## Table of Contents
1. System Overview
2. Architecture Diagram
3. Component Description
4. Data Flow
5. Technology Choices
6. Scalability Considerations
7. System Workflow

---

## 1. System Overview

### Problem Definition
Customer support teams face challenges with:
- **High Volume**: Handling thousands of inquiries manually
- **Response Time**: Slow turnaround on customer issues
- **Consistency**: Inconsistent answers across support staff
- **Knowledge Base Access**: Difficulty finding relevant information quickly

### Solution Approach
A **Retrieval-Augmented Generation (RAG)** system that:
- Automatically retrieves relevant knowledge from documents
- Generates contextual responses using LLMs
- Provides routing decisions through a graph-based workflow
- Escalates complex queries to human agents

### System Scope
- **Input**: Customer queries (text)
- **Processing**: Document retrieval, answer generation, confidence evaluation
- **Output**: Direct answer or escalation with ticket
- **Integration**: Human-in-the-Loop for escalation handling

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOMER SUPPORT ASSISTANT                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                               │
│  │  User Input  │                                               │
│  │  (Query)     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        LANGGRAPH WORKFLOW ORCHESTRATION                  │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                            │  │
│  │  ┌─────────────────┐      ┌──────────────────────────┐  │  │
│  │  │ Node 1: RETRIEVE│ ───► │ Retrieval Layer         │  │  │
│  │  └────────┬────────┘      └──────────┬───────────────┘  │  │
│  │           │                          │                   │  │
│  │  ┌────────▼────────┐      ┌──────────▼───────────────┐  │  │
│  │  │Node 2: GENERATE │ ───► │ LLM Processing Layer    │  │  │
│  │  └────────┬────────┘      │ (OpenAI/Hugging Face)   │  │  │
│  │           │                └──────────┬───────────────┘  │  │
│  │  ┌────────▼────────┐      ┌──────────▼───────────────┐  │  │
│  │  │ Node 3: EVALUATE│ ───► │ Confidence Calculator   │  │  │
│  │  └────────┬────────┘      └──────────┬───────────────┘  │  │
│  │           │                          │                   │  │
│  │           └──────────────┬───────────┘                   │  │
│  │                          │                               │  │
│  │                  ┌───────▼────────┐                      │  │
│  │                  │ Conditional    │                      │  │
│  │                  │ Router         │                      │  │
│  │                  └───┬────────┬───┘                      │  │
│  │                      │        │                          │  │
│  │         Confidence   │        │   Low Confidence        │  │
│  │         High (>0.4)  │        │   (<0.4)                │  │
│  │                      │        │                          │  │
│  └──────────┬───────────┘        └──────────┬──────────────┘  │
│             │                               │                  │
│             ▼                               ▼                  │
│  ┌──────────────────┐            ┌──────────────────────┐    │
│  │ Direct Response  │            │  HITL Escalation     │    │
│  │                  │            │                      │    │
│  │ Send Answer to   │            │ Create Ticket        │    │
│  │ Customer         │            │ Notify Human         │    │
│  └──────────┬───────┘            │ Wait for Response    │    │
│             │                     └──────────┬──────────┘    │
│             │                               │                 │
│             └───────────────┬───────────────┘                 │
│                             │                                 │
│                             ▼                                 │
│                    ┌──────────────────┐                       │
│                    │  Final Response  │                       │
│                    │  to Customer     │                       │
│                    └──────────────────┘                       │
│                                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   DOCUMENT INGESTION PIPELINE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────┐   │
│  │ PDF Documents│ ──►│   Chunking   │ ──►│  Embeddings    │   │
│  │              │    │              │    │  Generation    │   │
│  └──────────────┘    └──────────────┘    └────────┬───────┘   │
│                                                     │            │
│                                              ┌──────▼────────┐  │
│                                              │  ChromaDB      │  │
│                                              │ (Vector Store) │  │
│                                              └────────┬───────┘  │
│                                                       │          │
│                                              ┌────────▼────────┐│
│                                              │ Persistent      ││
│                                              │ Vector Storage  ││
│                                              └─────────────────┘│
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Description

### 3.1 Document Loader
**Purpose**: Load and preprocess PDF documents
- Reads PDF files from the designated data directory
- Extracts text content page by page
- Preserves metadata (source file, page number)
- Handles errors gracefully

**Key Features**:
- Batch processing of multiple PDFs
- Automatic error handling
- Page-level tracking
- Source attribution

### 3.2 Chunking Strategy
**Purpose**: Break documents into manageable pieces
- **Chunk Size**: 500 characters per chunk
- **Overlap**: 100 characters between chunks
- **Rationale**: 
  - Balances context preservation with computational efficiency
  - Overlap ensures continuity across chunk boundaries
  - Suitable for embeddings (typically 384-768 dimensions)

**Algorithm**:
```
1. Clean text (remove extra whitespace)
2. If text length ≤ chunk_size: return as single chunk
3. Otherwise:
   - Calculate step = chunk_size - overlap
   - Slide window across text with step size
   - Preserve metadata for each chunk
```

### 3.3 Embedding Model
**Purpose**: Convert text to vector representations
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Advantages**:
  - Lightweight (33MB)
  - Fast inference
  - Good semantic understanding
  - No API key required (runs locally)
- **Output**: 384-dimensional vectors
- **Computation**: Batch processing with progress tracking

### 3.4 Vector Store (ChromaDB)
**Purpose**: Store and retrieve embeddings efficiently
- **Database**: ChromaDB (SQLite-based)
- **Persistence**: Local disk storage
- **Similarity Metric**: Cosine similarity
- **Advantages**:
  - Easy to set up and use
  - Built-in similarity search
  - Persistent storage
  - No additional infrastructure needed

**Operations**:
- `add_embeddings()`: Store new embeddings
- `query()`: Retrieve similar documents
- `get_stats()`: Collection statistics
- `clear_collection()`: Reset database

### 3.5 Retrieval Layer
**Purpose**: Find relevant documents for queries
- Generates query embedding (same model as documents)
- Searches vector store using cosine similarity
- Returns top-K most similar documents
- Calculates confidence scores based on distance

**Retrieval Process**:
1. Embed the query
2. Search vector store
3. Convert distances to confidence scores
4. Format results with metadata

### 3.6 LLM Processing Layer
**Purpose**: Generate contextual answers
- **Model**: GPT-3.5-turbo (or replaceable with open-source)
- **Temperature**: 0.7 (balanced creativity and consistency)
- **Max Tokens**: 500 (prevents verbose responses)
- **Prompt Strategy**: Few-shot with context

**Process**:
1. Construct prompt with context
2. Include system instructions
3. Send to LLM
4. Parse and return response

### 3.7 Workflow Orchestration (LangGraph)
**Purpose**: Control the flow of query processing
- **Nodes**:
  - **Retrieve**: Get relevant documents
  - **Generate**: Create answer
  - **Evaluate**: Check confidence
  - **Escalate/Respond**: Route to appropriate action
  
- **State Management**: Maintains data between nodes
- **Conditional Routing**: Routes based on confidence scores
- **Error Handling**: Handles failures at each node

### 3.8 Routing Layer
**Purpose**: Decide between direct response and escalation
- **Criteria for Direct Response**:
  - Confidence score ≥ 0.4
  - First or second attempt
  - Clear context available
  
- **Criteria for Escalation**:
  - Confidence score < 0.4
  - Multiple failed attempts
  - No relevant context
  - User explicitly requests human support

### 3.9 HITL Module
**Purpose**: Manage human escalation and intervention
- **Escalation Management**: Create and track tickets
- **Ticket System**: Unique ID, timestamp, status tracking
- **Ticket Fields**:
  - Query
  - Retrieved context
  - AI attempted response
  - Escalation reason
  - Human response
  - Resolution status
  
- **Statistics**: Track escalation patterns
- **Resolution**: Document human responses

---

## 4. Data Flow

### Query Lifecycle

```
┌─────────────────────┐
│  User Query Input   │
│  "How do I reset    │
│   my password?"     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  1. EMBEDDING GENERATION                │
│  - Query: "How do I reset my password?" │
│  - Embedding: [0.23, -0.15, 0.82, ...] │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  2. VECTOR SEARCH                       │
│  - Search ChromaDB                      │
│  - Find top-3 similar documents         │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  3. CONTEXT RETRIEVAL                   │
│  - Retrieved Context:                   │
│    "Go to Settings → Account            │
│     Click 'Forgot Password'              │
│     Check email for link..."             │
│  - Confidence Scores:                   │
│    [0.85, 0.72, 0.65]                   │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  4. LLM PROCESSING                      │
│  - System Prompt: You are a             │
│    helpful support agent...              │
│  - User Query + Context → LLM           │
│  - Output: "To reset your               │
│    password, follow these steps..."     │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  5. CONFIDENCE EVALUATION               │
│  - Base Confidence: 0.79                │
│  - Response indicators: Clear            │
│  - Final Confidence: 0.79               │
└──────────┬──────────────────────────────┘
           │
           ▼
     ┌─────┴─────┐
     │           │
  HIGH (>0.4) LOW (<0.4)
     │           │
     ▼           ▼
  RESPOND    ESCALATE
     │           │
     ▼           ▼
┌──────────┐  ┌─────────────────────┐
│  Direct  │  │  Create Escalation  │
│ Answer   │  │  Ticket             │
│  To User │  │  Notify Human Agent │
└──────────┘  └─────────────────────┘
```

---

## 5. Technology Choices

### 5.1 ChromaDB (Vector Database)
**Why ChromaDB?**
- **Simplicity**: No external infrastructure
- **Performance**: Fast similarity search
- **Persistence**: Reliable data storage
- **Developer Friendly**: Easy API
- **Cost Effective**: Open-source, no licensing

**Alternatives Considered**:
- Pinecone: Expensive, external dependency
- Weaviate: More complex setup
- Milvus: Requires separate service

### 5.2 LangGraph (Workflow Orchestration)
**Why LangGraph?**
- **Graph-based**: Natural representation of workflows
- **Conditional Routing**: Built-in decision logic
- **State Management**: Clear data flow between nodes
- **Error Handling**: Robust error management
- **Debugging**: Excellent debugging capabilities

**Why Not Traditional Flow Control?**
- If-else chains become unmanageable at scale
- Graph representation is more intuitive
- Easier to add new routes/conditions
- Better for complex decision logic

### 5.3 LLM Choice: GPT-3.5-turbo
**Rationale**:
- **Cost**: Competitive pricing ($0.0005-0.0015 per 1K tokens)
- **Performance**: Fast inference
- **Quality**: State-of-the-art generation quality
- **Reliability**: Consistent output

**Alternative Options**:
- Llama 2 (local, privacy-focused)
- Claude 2 (better quality, higher cost)
- Mistral 7B (efficient, open-source)

### 5.4 Embedding Model: Sentence-Transformers
**Why Sentence-Transformers?**
- **Open Source**: No API costs
- **Fast**: Local inference
- **Good Quality**: Trained on semantic tasks
- **Efficient**: Small model size (33MB)
- **Privacy**: All processing local

---

## 6. Scalability Considerations

### 6.1 Handling Large Documents
**Challenge**: Processing 1000+ page documents
**Solutions**:
- **Incremental Indexing**: Add documents in batches
- **Batch Chunking**: Process chunks in parallel
- **Async Processing**: Non-blocking embedding generation
- **Compression**: Store compressed vectors

### 6.2 Increasing Query Load
**Challenge**: Handle 1000+ queries/hour
**Solutions**:
- **Caching**: Store frequently asked queries
- **Query Batching**: Process multiple queries together
- **Load Balancing**: Distribute across multiple instances
- **Async Processing**: Non-blocking query handling

### 6.3 Latency Concerns
**Current Performance**:
- Query embedding: ~50ms
- Vector search: ~20ms
- LLM inference: ~2-3 seconds
- Total: ~3-4 seconds per query

**Optimization Strategies**:
- Use faster embedding model
- Implement query caching
- Reduce top-K retrieval
- Batch LLM requests
- Use edge computing for embeddings

### 6.4 Memory Management
**Vector Store Size**:
- 1000 documents × 5 chunks = 5000 vectors
- 5000 × 384 dimensions × 4 bytes = ~7.7 MB
- Highly scalable

**Scalability Limits**:
- Single instance: 100K+ documents feasible
- Distributed setup: Unlimited with proper architecture

---

## 7. System Workflow

### Complete Query Processing Flow

```
1. INPUT PHASE
   ├─ User submits query
   ├─ Query validation
   └─ Initialize request context

2. RETRIEVAL PHASE
   ├─ Generate query embedding
   ├─ Search vector store (ChromaDB)
   ├─ Retrieve top-3 documents
   ├─ Calculate confidence scores
   └─ Format context

3. GENERATION PHASE
   ├─ Prepare LLM prompt
   ├─ Include system instructions
   ├─ Include retrieved context
   ├─ Call LLM API
   └─ Parse response

4. EVALUATION PHASE
   ├─ Calculate confidence score
   ├─ Check for uncertainty indicators
   ├─ Evaluate attempt count
   └─ Determine routing decision

5. ROUTING PHASE
   ├─ If confidence > 0.4 AND attempt < 2
   │  └─ Route to DIRECT_RESPONSE
   └─ Else
      └─ Route to ESCALATION

6. RESPONSE/ESCALATION PHASE
   ├─ Direct Response:
   │  ├─ Format answer
   │  ├─ Include sources
   │  └─ Send to user
   └─ Escalation:
      ├─ Create HITL ticket
      ├─ Notify human agent
      ├─ Store ticket
      └─ Send confirmation to user

7. OUTPUT PHASE
   ├─ Return response to user
   ├─ Log interaction
   ├─ Update statistics
   └─ End request
```

---

## 8. Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Easy to add new LLMs, vector stores, or routing rules
3. **Reliability**: Graceful degradation and error handling
4. **Transparency**: Clear logging and auditing
5. **User-Centric**: Prioritizes user experience and satisfaction
6. **Privacy**: Local processing where possible
7. **Cost-Effective**: Balances quality with operational cost

---

## 9. Key Features

✓ Automatic document ingestion and processing
✓ Semantic search using embeddings
✓ Graph-based workflow with conditional routing
✓ Confidence-based escalation
✓ Human-in-the-Loop support
✓ Ticket tracking and management
✓ Extensible architecture
✓ Error handling and logging
✓ Performance monitoring

---

## 10. Assumptions & Constraints

**Assumptions**:
- OpenAI API key available for LLM calls
- Document formats: PDF files
- Query language: English
- Single user for demo

**Constraints**:
- Requires internet for LLM calls
- Local vector store (not distributed)
- Single instance deployment
- 500-character chunk size (configurable)

---

**Document Version**: 1.0
**Date**: 2024
**Status**: Design Phase Complete
