"""
Recommendation Agent
Uses RAG to search facilities and provide recommendations.
Can incorporate insights from other agents (medical desert data, trust scores)
for richer, cross-agent-aware responses.
"""

from typing import Dict
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def recommendation_agent(state: Dict) -> Dict:
    """
    Recommendation agent node.
    1) Retrieves relevant facilities via RAG semantic search.
    2) Checks for cross-agent data (desert analysis, trust scores).
    3) Uses LLM to generate a recommendation that integrates all available context.
    Stores its output in agent_outputs for multi-agent coordination.
    """
    from backend.agents.tools import search_healthcare_facilities

    messages = state["messages"]

    # Extract query
    query = messages[-1].content

    # 1. RETRIEVE: Search for facilities using RAG
    search_results = search_healthcare_facilities.invoke({
        "query": query,
        "top_k": 5
    })

    # 2. AUGMENT: Build context with cross-agent data
    cross_agent_context = ""
    agent_outputs = state.get("agent_outputs") or {}

    if "medical_desert" in agent_outputs:
        cross_agent_context += (
            "\n\n=== MEDICAL DESERT ANALYSIS (from specialist agent) ===\n"
            f"{agent_outputs['medical_desert'][:500]}\n"
        )

    if "trust_scoring" in agent_outputs:
        cross_agent_context += (
            "\n\n=== TRUST SCORING (from specialist agent) ===\n"
            f"{agent_outputs['trust_scoring'][:500]}\n"
        )

    system_prompt = """You are the CareConnect AI, an expert on healthcare facilities in Ghana.
Your goal is to recommend facilities based on the user's needs using the provided search results.

GUIDELINES:
- ALWAYS answer based on the "Search Results" provided below.
- If cross-agent data is available (medical desert analysis, trust scores), incorporate those insights into your recommendations.
- If the user asks a follow-up question, use conversation context to maintain continuity.
- Be helpful, professional, and concise.
- If no facilities match, say so clearly and suggest broadening the search.
- Highlight key info: Name, Location, Specialties, and Contact Info.
- If trust scores are available from the trust agent, mention them.
- If medical desert data is available, factor regional access into recommendations.
- Use markdown formatting for readability."""

    # Format search results for the LLM
    context_str = f"\n\n=== RELEVANT SEARCH RESULTS ===\n{search_results}\n==============================="

    if cross_agent_context:
        context_str += f"\n{cross_agent_context}"

    # Construct message history for context window
    conversation = [SystemMessage(content=system_prompt)]

    # Add previous messages (limiting to last 5 for context window)
    if len(messages) > 1:
        # Skip the very last message as we'll add it with context
        conversation.extend(messages[-6:-1])

    # Add latest user query with context
    final_user_message = (
        f"User Query: {query}\n{context_str}\n\n"
        "Please provide a helpful answer based on these results."
    )
    conversation.append(HumanMessage(content=final_user_message))

    # 3. GENERATE: Get response from LLM
    response = llm.invoke(conversation)

    response_text = response.content

    # Store output for multi-agent coordination
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_outputs["recommendation"] = response_text

    return {
        "messages": [response],
        "current_agent": "recommendation",
        "agent_outputs": agent_outputs
    }
