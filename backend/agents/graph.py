"""
LangGraph Agent Orchestration
Main agent graph with LLM-based routing, multi-agent coordination,
and a synthesizer for combining results from multiple agents.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from backend.agents.state import AgentState
from backend.agents.recommendation_agent import recommendation_agent
from backend.agents.medical_desert_agent import medical_desert_agent
from backend.agents.trust_scoring_agent import trust_scoring_agent

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Shared LLM instance for router and synthesizer
_router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def router_node(state: AgentState) -> dict:
    """
    LLM-based router node - classifies user intent and determines
    which agent(s) should handle the query.
    Supports multi-agent routing for complex queries.
    Falls back to keyword matching if the LLM call fails.
    """
    messages = state["messages"]
    last_message = messages[-1].content

    try:
        # Build conversation context for follow-up awareness
        recent_context = ""
        if len(messages) > 1:
            recent_msgs = messages[-4:-1]
            context_parts = []
            for msg in recent_msgs:
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                context_parts.append(f"{role}: {msg.content[:200]}")
            recent_context = "\n\nRecent conversation:\n" + "\n".join(context_parts)

        classification_prompt = f"""You are the CareConnect AI router. Analyze the user's query and determine which agent(s) should handle it.

Available agents:
1. medical_desert - Analyzes regional healthcare distribution, identifies underserved areas, compares regions, medical deserts
2. trust_scoring - Calculates trust/reliability scores for specific healthcare facilities, verifies data quality
3. recommendation - Searches and recommends healthcare facilities based on user needs using semantic search (RAG)

Rules:
- If the query is about regional coverage, gaps, underserved areas, or distribution → medical_desert
- If the query is about verifying, trusting, or scoring a specific facility → trust_scoring
- If the query is about finding, recommending, or searching for facilities → recommendation
- If the query needs multiple agents, list them in execution order separated by commas
  Example: "Find a trustworthy hospital" → recommendation,trust_scoring
  Example: "Which underserved regions need more hospitals?" → medical_desert,recommendation
- For simple greetings or unclear queries → recommendation

Return ONLY a comma-separated list of agent names. No explanations.
{recent_context}"""

        response = _router_llm.invoke([
            SystemMessage(content=classification_prompt),
            HumanMessage(content=f"User query: {last_message}")
        ])

        # Parse agent list from LLM response
        agent_names = [a.strip() for a in response.content.strip().split(",")]
        valid_agents = {"medical_desert", "trust_scoring", "recommendation"}
        agent_names = [a for a in agent_names if a in valid_agents]

        if not agent_names:
            agent_names = ["recommendation"]

    except Exception:
        # Fallback to keyword-based routing if LLM fails
        last_lower = last_message.lower()
        desert_keywords = ["desert", "underserved", "region", "distribution", "coverage", "gap", "which regions"]
        trust_keywords = ["trust", "verify", "reliable", "suspicious", "score", "trustworthy", "quality"]

        if any(k in last_lower for k in desert_keywords):
            agent_names = ["medical_desert"]
        elif any(k in last_lower for k in trust_keywords):
            agent_names = ["trust_scoring"]
        else:
            agent_names = ["recommendation"]

    # All agents go into the queue; the dispatcher will pop them one by one
    return {
        "user_intent": agent_names[0],
        "agents_to_run": agent_names,
        "agent_outputs": {}
    }


def dispatcher_node(state: AgentState) -> dict:
    """
    Dispatcher - pops the next agent from the queue.
    If the queue is empty, signals 'done' so the graph routes to the synthesizer.
    """
    agents_to_run = list(state.get("agents_to_run") or [])

    if agents_to_run:
        next_agent = agents_to_run.pop(0)
        return {
            "current_agent": next_agent,
            "agents_to_run": agents_to_run
        }

    return {
        "current_agent": "done"
    }


def route_from_dispatcher(
    state: AgentState,
) -> Literal["medical_desert", "trust_scoring", "recommendation", "synthesizer"]:
    """
    Conditional edge function - routes from the dispatcher to the
    appropriate agent node, or to the synthesizer when all agents are done.
    """
    current = state.get("current_agent", "done")
    if current in ("medical_desert", "trust_scoring", "recommendation"):
        return current
    return "synthesizer"


def synthesizer_node(state: AgentState) -> dict:
    """
    Synthesizer - combines results from multiple agents into one coherent response.
    Only generates a new message when two or more agents produced output.
    For single-agent runs it passes through without adding a message.
    """
    agent_outputs = state.get("agent_outputs") or {}

    # Single agent (or zero) — nothing to synthesize
    if len(agent_outputs) <= 1:
        return {}

    # Build combined context from every agent that ran
    context_parts = []
    for agent_name, output in agent_outputs.items():
        label = agent_name.replace("_", " ").title()
        context_parts.append(f"=== {label} Agent Results ===\n{output}")
    combined_context = "\n\n".join(context_parts)

    # Recover the original user query
    user_query = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    synthesis_prompt = """You are the CareConnect AI synthesizer. Multiple specialist agents have analyzed the user's query.
Your job is to combine their findings into a single, coherent, and helpful response.

Guidelines:
- Integrate insights from all agents naturally into one unified answer
- Highlight connections between findings (e.g., a region is a medical desert AND its facilities have low trust scores)
- Don't just concatenate results — weave them together meaningfully
- Be concise but comprehensive
- Use markdown formatting for readability
- Address the user's original question directly"""

    response = _router_llm.invoke([
        SystemMessage(content=synthesis_prompt),
        HumanMessage(
            content=(
                f"User's Original Query: {user_query}\n\n"
                f"{combined_context}\n\n"
                "Please provide a unified, coherent response that combines all these findings."
            )
        )
    ])

    return {
        "messages": [response]
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

# Global graph instance (singleton)
_graph = None


def get_agent_graph():
    """
    Get or create the singleton agent graph.

    Graph topology:
        START → router → dispatcher ──┬── medical_desert ──┐
                                       ├── trust_scoring  ──┤
                                       ├── recommendation ──┤
                                       └── synthesizer ─────┘
                                              ▲               │
                                              └── dispatcher ◄┘
                                                     │
                                              synthesizer → END

    The dispatcher loop allows multiple agents to run in sequence,
    each able to see the previous agent's outputs through shared state.
    """
    global _graph

    if _graph is not None:
        return _graph

    # Create workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("dispatcher", dispatcher_node)
    workflow.add_node("medical_desert", medical_desert_agent)
    workflow.add_node("trust_scoring", trust_scoring_agent)
    workflow.add_node("recommendation", recommendation_agent)
    workflow.add_node("synthesizer", synthesizer_node)

    # Entry point
    workflow.add_edge(START, "router")

    # Router feeds into dispatcher
    workflow.add_edge("router", "dispatcher")

    # Dispatcher routes to the appropriate agent or to the synthesizer
    workflow.add_conditional_edges(
        "dispatcher",
        route_from_dispatcher,
        {
            "medical_desert": "medical_desert",
            "trust_scoring": "trust_scoring",
            "recommendation": "recommendation",
            "synthesizer": "synthesizer",
        }
    )

    # After each agent finishes, loop back to the dispatcher
    workflow.add_edge("medical_desert", "dispatcher")
    workflow.add_edge("trust_scoring", "dispatcher")
    workflow.add_edge("recommendation", "dispatcher")

    # Synthesizer terminates the graph
    workflow.add_edge("synthesizer", END)

    # In-memory checkpointer for conversation persistence
    checkpointer = MemorySaver()

    _graph = workflow.compile(checkpointer=checkpointer)
    return _graph


def invoke_agent(query: str, thread_id: str = "default") -> str:
    """
    Convenient wrapper to invoke the agent graph.

    Args:
        query: User query
        thread_id: Conversation thread ID for persistence

    Returns:
        Agent response as string
    """
    graph = get_agent_graph()

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config
    )

    # Return the last AI message (either a single agent's or the synthesizer's)
    if result["messages"]:
        return result["messages"][-1].content
    return "No response generated"


if __name__ == "__main__":
    # Test the agent system
    print("Testing CareConnect Agent System...\n")

    # Test 1: Medical desert query
    print("=" * 70)
    print("TEST 1: Medical Desert Analysis")
    print("=" * 70)
    response = invoke_agent("Which regions in Ghana are medical deserts?", thread_id="test_1")
    print(response)
    print()

    # Test 2: Trust scoring query
    print("=" * 70)
    print("TEST 2: Trust Scoring")
    print("=" * 70)
    response = invoke_agent("What's the trust score for Korle Bu Teaching Hospital?", thread_id="test_2")
    print(response)
    print()

    # Test 3: Recommendation query
    print("=" * 70)
    print("TEST 3: Facility Recommendation")
    print("=" * 70)
    response = invoke_agent("Find me the best pediatric hospital in Accra", thread_id="test_3")
    print(response)
    print()

    # Test 4: Multi-agent query (recommendation + trust scoring)
    print("=" * 70)
    print("TEST 4: Multi-Agent (Recommendation + Trust)")
    print("=" * 70)
    response = invoke_agent("Find me a trustworthy eye hospital in Accra", thread_id="test_4")
    print(response)
