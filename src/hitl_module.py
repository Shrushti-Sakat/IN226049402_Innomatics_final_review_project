"""
HITL (Human-in-the-Loop) Module
Handles escalation and human intervention
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class EscalationReason(Enum):
    """Reasons for escalation"""
    LOW_CONFIDENCE = "low_confidence"
    NO_CONTEXT = "no_context"
    COMPLEX_QUERY = "complex_query"
    MULTIPLE_ATTEMPTS = "multiple_attempts"
    USER_REQUEST = "user_request"


@dataclass
class EscalationTicket:
    """Escalation ticket for human review"""
    ticket_id: str
    query: str
    retrieved_context: str
    ai_response: str
    ai_confidence: float
    escalation_reason: str
    timestamp: str
    status: str = "pending"  # pending, resolved, closed
    human_response: Optional[str] = None


class HITLManager:
    """Manage Human-in-the-Loop escalations"""
    
    def __init__(self):
        """Initialize HITLManager"""
        self.tickets: Dict[str, EscalationTicket] = {}
        self.ticket_counter = 0
    
    def should_escalate(self, confidence: float, attempt_count: int, 
                       reason: Optional[str] = None) -> bool:
        """
        Determine if a query should be escalated to human
        
        Args:
            confidence: Confidence score of the answer
            attempt_count: Number of attempts made
            reason: Additional reason context
            
        Returns:
            True if should escalate
        """
        # Escalate if confidence is too low
        if confidence < 0.4:
            return True
        
        # Escalate if too many attempts
        if attempt_count >= 2:
            return True
        
        # Escalate if explicit complex query signal
        if reason and "complex" in reason.lower():
            return True
        
        return False
    
    def create_escalation(self, query: str, context: str, ai_response: str,
                         confidence: float, reason: EscalationReason) -> EscalationTicket:
        """
        Create an escalation ticket
        
        Args:
            query: User query
            context: Retrieved context
            ai_response: AI generated response
            confidence: Confidence score
            reason: Reason for escalation
            
        Returns:
            EscalationTicket object
        """
        self.ticket_counter += 1
        ticket_id = f"ESCALATION-{self.ticket_counter:05d}"
        
        ticket = EscalationTicket(
            ticket_id=ticket_id,
            query=query,
            retrieved_context=context,
            ai_response=ai_response,
            ai_confidence=confidence,
            escalation_reason=reason.value,
            timestamp=datetime.now().isoformat()
        )
        
        self.tickets[ticket_id] = ticket
        print(f"Created escalation ticket: {ticket_id}")
        
        return ticket
    
    def resolve_ticket(self, ticket_id: str, human_response: str) -> Dict:
        """
        Resolve an escalation ticket with human response
        
        Args:
            ticket_id: ID of the ticket
            human_response: Human's response
            
        Returns:
            Updated ticket information
        """
        if ticket_id not in self.tickets:
            return {"error": f"Ticket {ticket_id} not found"}
        
        ticket = self.tickets[ticket_id]
        ticket.status = "resolved"
        ticket.human_response = human_response
        
        print(f"Resolved ticket: {ticket_id}")
        
        return asdict(ticket)
    
    def get_pending_tickets(self) -> List[Dict]:
        """
        Get all pending escalation tickets
        
        Returns:
            List of pending tickets
        """
        pending = [
            asdict(ticket) for ticket in self.tickets.values()
            if ticket.status == "pending"
        ]
        return pending
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """
        Get a specific ticket
        
        Args:
            ticket_id: ID of the ticket
            
        Returns:
            Ticket information or None
        """
        if ticket_id in self.tickets:
            return asdict(self.tickets[ticket_id])
        return None
    
    def get_statistics(self) -> Dict:
        """Get escalation statistics"""
        total = len(self.tickets)
        pending = sum(1 for t in self.tickets.values() if t.status == "pending")
        resolved = sum(1 for t in self.tickets.values() if t.status == "resolved")
        
        return {
            "total_escalations": total,
            "pending": pending,
            "resolved": resolved,
            "closed": total - pending - resolved
        }
