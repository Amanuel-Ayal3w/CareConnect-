"""
Agent state definition for CareConnect LangGraph agents
Supports multi-agent coordination and inter-agent communication
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State for CareConnect multi-agent system"""
    
    # Conversation messages with reducer to append new messages
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Analysis results from different agents
    medical_desert_data: dict | None  # Regional analysis results
    trust_scores: dict | None  # Facility trust scores
    facility_results: list | None  # Search results from RAG
    
    # Multi-agent coordination
    current_agent: str  # Which agent is currently active / next to run
    user_intent: str | None  # Primary detected intent
    agents_to_run: list | None  # Queue of agents still to execute
    agent_outputs: dict | None  # Collected text outputs keyed by agent name
    
    # Filters
    region_filter: str | None  # Region being analyzed
    facility_filter: str | None  # Facility being verified
    
    # Final outputs
    recommendation: str | None  # Final recommendation text
    next_steps: list | None  # Suggested actions for user
    confidence_score: float | None  # Agent confidence in response
