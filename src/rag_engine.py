"""
RAG Engine Module
Core logic for the RAG system
"""

from typing import Dict, Optional
from openai import OpenAI
from config import (
    OPENAI_API_KEY, 
    SYSTEM_PROMPT, 
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    CONFIDENCE_THRESHOLD
)
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from retriever import Retriever
from hitl_module import HITLManager, EscalationReason


class RAGEngine:
    """Core RAG Engine"""
    
    def __init__(self, embedding_gen: EmbeddingGenerator = None, 
                 vector_store: VectorStore = None):
        """
        Initialize RAG Engine
        
        Args:
            embedding_gen: EmbeddingGenerator instance
            vector_store: VectorStore instance
        """
        self.embedding_gen = embedding_gen or EmbeddingGenerator()
        self.vector_store = vector_store or VectorStore()
        self.retriever = Retriever(self.embedding_gen, self.vector_store)
        self.hitl_manager = HITLManager()
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        
        self.attempt_count = {}  # Track attempts per query
    
    def process_query(self, query: str, enable_hitl: bool = True) -> Dict:
        """
        Process a customer support query end-to-end
        
        Args:
            query: User query
            enable_hitl: Whether to enable HITL escalation
            
        Returns:
            Response with answer and metadata
        """
        # Initialize attempt counter for this query
        if query not in self.attempt_count:
            self.attempt_count[query] = 0
        self.attempt_count[query] += 1
        
        # Step 1: Retrieve relevant documents
        retrieval_result = self.retriever.retrieve(query)
        context = self.retriever.format_context(retrieval_result)
        
        # Step 2: Generate answer using LLM
        llm_response = self._generate_answer(query, context, retrieval_result)
        
        # Step 3: Evaluate confidence and determine if escalation needed
        confidence = self._calculate_confidence(retrieval_result, llm_response)
        
        should_escalate = (
            enable_hitl and 
            self.hitl_manager.should_escalate(
                confidence,
                self.attempt_count[query],
                None
            )
        )
        
        if should_escalate:
            # Create escalation ticket
            ticket = self.hitl_manager.create_escalation(
                query=query,
                context=context,
                ai_response=llm_response["answer"],
                confidence=confidence,
                reason=self._determine_escalation_reason(retrieval_result, confidence)
            )
            
            return {
                "status": "escalated",
                "query": query,
                "answer": f"Your query has been escalated to our support team. Ticket ID: {ticket.ticket_id}",
                "ticket_id": ticket.ticket_id,
                "confidence": confidence,
                "ai_response": llm_response["answer"],
                "context_used": len(retrieval_result["documents"]),
                "reasoning": "The query requires human expertise for a better response."
            }
        
        return {
            "status": "success",
            "query": query,
            "answer": llm_response["answer"],
            "confidence": confidence,
            "sources": [doc["metadata"].get("source_file", "Unknown") 
                       for doc in retrieval_result["documents"]],
            "context_used": len(retrieval_result["documents"]),
            "model": llm_response.get("model"),
            "direct_answer": True
        }
    
    def _generate_answer(self, query: str, context: str, retrieval_result: Dict) -> Dict:
        """
        Generate answer using OpenAI GPT
        
        Args:
            query: User query
            context: Retrieved context
            retrieval_result: Retrieval results
            
        Returns:
            Generated answer and metadata
        """
        if not context or context == "No relevant documents found.":
            return {
                "answer": "I don't have enough information in the knowledge base to answer this question. Please contact our support team for further assistance.",
                "model": "fallback"
            }
        
        prompt = f"""System: {SYSTEM_PROMPT}

Knowledge Base Context:
{context}

Customer Question: {query}

Based on the knowledge base provided above, please answer the customer's question. If the answer is not in the knowledge base, clearly state that."""
        
        try:
            if not self.client:
                return {
                    "answer": "OpenAI API key not configured. Using fallback response.",
                    "model": "fallback"
                }
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "model": "gpt-3.5-turbo",
                "tokens_used": response.usage.total_tokens
            }
        
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            return {
                "answer": "I encountered an error while processing your request. Please try again or contact support.",
                "model": "error",
                "error": str(e)
            }
    
    def _calculate_confidence(self, retrieval_result: Dict, llm_response: Dict) -> float:
        """
        Calculate confidence score for the answer
        
        Args:
            retrieval_result: Retrieval results
            llm_response: LLM response
            
        Returns:
            Confidence score [0, 1]
        """
        # Base confidence on retrieval results
        if not retrieval_result["documents"]:
            return 0.0
        
        # Average confidence of top results
        avg_confidence = sum(doc["confidence"] for doc in retrieval_result["documents"]) / len(retrieval_result["documents"])
        
        # Check for uncertainty indicators in response
        uncertainty_phrases = ["i'm not sure", "i don't know", "unclear", "not specified"]
        response_text = llm_response.get("answer", "").lower()
        
        has_uncertainty = any(phrase in response_text for phrase in uncertainty_phrases)
        
        if has_uncertainty:
            avg_confidence *= 0.6  # Reduce confidence if response indicates uncertainty
        
        return min(1.0, avg_confidence)
    
    def _determine_escalation_reason(self, retrieval_result: Dict, confidence: float) -> EscalationReason:
        """
        Determine the reason for escalation
        
        Args:
            retrieval_result: Retrieval results
            confidence: Confidence score
            
        Returns:
            EscalationReason enum
        """
        if not retrieval_result["documents"]:
            return EscalationReason.NO_CONTEXT
        
        if confidence < 0.4:
            return EscalationReason.LOW_CONFIDENCE
        
        return EscalationReason.COMPLEX_QUERY
