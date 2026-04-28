"""
LangGraph Workflow Module
Implements the graph-based workflow for query processing
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from rag_engine import RAGEngine


@dataclass
class GraphState:
    """State object for the workflow graph"""
    query: str
    retrieved_context: Optional[str] = None
    ai_response: Optional[str] = None
    confidence: float = 0.0
    should_escalate: bool = False
    final_response: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RAGWorkflow:
    """LangGraph-based workflow for RAG processing"""
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize RAGWorkflow
        
        Args:
            rag_engine: RAGEngine instance
        """
        self.rag_engine = rag_engine
        self.graph_steps = []
    
    def process_query_workflow(self, query: str, enable_hitl: bool = True) -> Dict:
        """
        Execute the workflow for processing a query
        
        Workflow:
        START -> RETRIEVE -> GENERATE -> EVALUATE -> [ESCALATE | RESPOND] -> END
        
        Args:
            query: User query
            enable_hitl: Enable Human-in-the-Loop
            
        Returns:
            Final response
        """
        # Initialize state
        state = GraphState(query=query)
        
        # Node 1: Retrieve relevant documents
        state = self._node_retrieve(state)
        
        # Node 2: Generate answer
        state = self._node_generate_answer(state)
        
        # Node 3: Evaluate and route
        state = self._node_evaluate_and_route(state, enable_hitl)
        
        # Node 4: Conditional routing
        if state.should_escalate:
            state = self._node_escalate(state)
        else:
            state = self._node_respond(state)
        
        # Record workflow execution
        self.graph_steps.append({
            "query": query,
            "steps": ["RETRIEVE", "GENERATE", "EVALUATE", 
                     "ESCALATE" if state.should_escalate else "RESPOND"],
            "final_response": state.final_response
        })
        
        return {
            "status": "completed",
            "query": query,
            "response": state.final_response,
            "confidence": state.confidence,
            "escalated": state.should_escalate,
            "metadata": state.metadata
        }
    
    def _node_retrieve(self, state: GraphState) -> GraphState:
        """
        Node 1: Retrieve relevant documents
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with retrieved context
        """
        retrieval_result = self.rag_engine.retriever.retrieve(state.query)
        context = self.rag_engine.retriever.format_context(retrieval_result)
        
        state.retrieved_context = context
        state.metadata["retrieval_count"] = len(retrieval_result["documents"])
        state.metadata["retrieval_result"] = retrieval_result
        
        print(f"[RETRIEVE] Retrieved {len(retrieval_result['documents'])} documents")
        
        return state
    
    def _node_generate_answer(self, state: GraphState) -> GraphState:
        """
        Node 2: Generate answer using LLM
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with AI response
        """
        retrieval_result = state.metadata.get("retrieval_result", {})
        llm_response = self.rag_engine._generate_answer(
            state.query,
            state.retrieved_context,
            retrieval_result
        )
        
        state.ai_response = llm_response.get("answer")
        state.metadata["model"] = llm_response.get("model")
        
        print(f"[GENERATE] Generated answer using {llm_response.get('model')}")
        
        return state
    
    def _node_evaluate_and_route(self, state: GraphState, enable_hitl: bool) -> GraphState:
        """
        Node 3: Evaluate confidence and determine routing
        
        Args:
            state: Current graph state
            enable_hitl: Enable HITL
            
        Returns:
            Updated state with evaluation
        """
        retrieval_result = state.metadata.get("retrieval_result", {})
        llm_response = {"answer": state.ai_response}
        
        confidence = self.rag_engine._calculate_confidence(retrieval_result, llm_response)
        state.confidence = confidence
        
        if enable_hitl:
            attempt_count = state.metadata.get("attempt_count", 1)
            state.should_escalate = self.rag_engine.hitl_manager.should_escalate(
                confidence, attempt_count
            )
        
        print(f"[EVALUATE] Confidence: {confidence:.2%}, Escalate: {state.should_escalate}")
        
        return state
    
    def _node_escalate(self, state: GraphState) -> GraphState:
        """
        Node 4a: Escalate to human
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with escalation
        """
        retrieval_result = state.metadata.get("retrieval_result", {})
        reason = self.rag_engine._determine_escalation_reason(
            retrieval_result,
            state.confidence
        )
        
        ticket = self.rag_engine.hitl_manager.create_escalation(
            query=state.query,
            context=state.retrieved_context,
            ai_response=state.ai_response,
            confidence=state.confidence,
            reason=reason
        )
        
        state.final_response = f"Your query has been escalated. Ticket ID: {ticket.ticket_id}"
        state.metadata["ticket_id"] = ticket.ticket_id
        
        print(f"[ESCALATE] Created ticket {ticket.ticket_id}")
        
        return state
    
    def _node_respond(self, state: GraphState) -> GraphState:
        """
        Node 4b: Provide response directly
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with final response
        """
        state.final_response = state.ai_response
        state.metadata["direct_response"] = True
        
        print(f"[RESPOND] Providing direct response")
        
        return state
    
    def get_workflow_history(self) -> list:
        """Get history of workflow executions"""
        return self.graph_steps
