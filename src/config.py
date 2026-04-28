"""
Configuration module for RAG Customer Support Assistant
"""

import os
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "sample_data"
DOCS_DIR = PROJECT_ROOT / "docs"
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

# Model and Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Open-source model
LLM_MODEL = "gpt-3.5-turbo"  # Can be replaced with open-source alternatives
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = "customer_support_docs"
CHROMA_PERSIST_DIRECTORY = str(CHROMA_DB_DIR)

# Chunking Strategy
CHUNK_SIZE = 500  # Number of characters per chunk
CHUNK_OVERLAP = 100  # Overlap between chunks for context preservation

# Retrieval Configuration
TOP_K_RESULTS = 3  # Number of top results to retrieve
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for answer generation

# HITL Configuration
HITL_ENABLED = True
ESCALATION_THRESHOLD = 0.4  # Below this, escalate to human
MAX_ATTEMPTS = 2  # Maximum AI attempts before escalation

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# System Prompts
SYSTEM_PROMPT = """You are a helpful customer support assistant. Your role is to:
1. Answer customer questions based on the provided knowledge base
2. Be accurate and helpful in your responses
3. Clearly state when you don't have information to answer a question
4. Suggest escalation when needed

When answering questions, always cite the relevant sections from the knowledge base."""

ESCALATION_PROMPT = """This query requires human intervention. The following information was available:
Query: {query}
Retrieved Context: {context}
AI Response Attempt: {ai_response}

Reason for escalation: {reason}

Please provide a more detailed or personalized response."""
