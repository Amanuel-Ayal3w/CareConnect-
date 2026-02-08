"""
Medical Desert Analyzer Agent
Identifies underserved regions and analyzes healthcare distribution.
Uses LLM for intelligent, contextual response generation from real data.
"""

from typing import Dict
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize LLM for analysis
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def analyze_regional_distribution() -> Dict:
    """
    Analyze healthcare facility distribution across all regions.
    Returns comprehensive statistics and medical desert identification.
    """
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get facility counts by region
    cursor.execute("""
        SELECT 
            COALESCE(address_state_or_region, 'Unknown') as region,
            COUNT(*) as total_facilities,
            COUNT(DISTINCT facility_type_id) as facility_types,
            COUNT(CASE WHEN facility_type_id = 'hospital' THEN 1 END) as hospitals,
            COUNT(CASE WHEN facility_type_id = 'clinic' THEN 1 END) as clinics
        FROM facilities
        GROUP BY address_state_or_region
        ORDER BY total_facilities ASC
    """)

    regions = cursor.fetchall()

    # Get specialty distribution by region
    cursor.execute("""
        SELECT 
            region,
            COUNT(DISTINCT specialty) as unique_specialties
        FROM (
            SELECT 
                COALESCE(address_state_or_region, 'Unknown') as region,
                jsonb_array_elements_text(specialties) as specialty
            FROM facilities
            WHERE specialties IS NOT NULL
        ) AS specialty_data
        GROUP BY region
    """)

    specialty_counts = {row['region']: row['unique_specialties'] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    # Calculate statistics
    if not regions:
        return {"error": "No regional data available"}

    total_facilities = sum(r['total_facilities'] for r in regions)
    avg_per_region = total_facilities / len(regions)

    # Identify medical deserts (< 50% of average)
    desert_threshold = avg_per_region * 0.5
    medical_deserts = [r for r in regions if r['total_facilities'] < desert_threshold]

    # Best served regions
    best_served = sorted(regions, key=lambda x: x['total_facilities'], reverse=True)[:3]

    return {
        'total_regions': len(regions),
        'total_facilities': total_facilities,
        'average_per_region': avg_per_region,
        'desert_threshold': desert_threshold,
        'medical_deserts': medical_deserts,
        'best_served': best_served,
        'all_regions': regions,
        'specialty_counts': specialty_counts
    }


def medical_desert_agent(state: Dict) -> Dict:
    """
    Medical desert analyzer agent node.
    Retrieves real data from the database, then uses the LLM to generate
    an intelligent, contextual analysis for the user.
    """
    messages = state["messages"]
    user_query = messages[-1].content

    # Check if user is asking about a specific region
    region_filter = state.get('region_filter')

    # Analyze distribution from database
    analysis = analyze_regional_distribution()

    if 'error' in analysis:
        response_text = "I'm sorry, I couldn't retrieve regional healthcare data at this time."
        agent_outputs = dict(state.get("agent_outputs") or {})
        agent_outputs["medical_desert"] = response_text
        return {
            "messages": [AIMessage(content=response_text)],
            "current_agent": "medical_desert",
            "agent_outputs": agent_outputs
        }

    # ---- Format raw data as context for the LLM ----
    data_parts = [
        f"Total Regions: {analysis['total_regions']}",
        f"Total Facilities: {analysis['total_facilities']}",
        f"Average per Region: {analysis['average_per_region']:.1f}",
        f"Desert Threshold (< 50% of avg): {analysis['desert_threshold']:.0f} facilities",
    ]

    if analysis['medical_deserts']:
        data_parts.append(
            f"\nIdentified Medical Deserts ({len(analysis['medical_deserts'])} regions):"
        )
        for desert in analysis['medical_deserts']:
            spec = analysis['specialty_counts'].get(desert['region'], 0)
            data_parts.append(
                f"  - {desert['region']}: {desert['total_facilities']} facilities "
                f"({desert['hospitals']} hospitals, {desert['clinics']} clinics, "
                f"{spec} specialties)"
            )

    data_parts.append("\nBest Served Regions:")
    for region in analysis['best_served']:
        spec = analysis['specialty_counts'].get(region['region'], 0)
        data_parts.append(
            f"  - {region['region']}: {region['total_facilities']} facilities "
            f"({region['hospitals']} hospitals, {region['clinics']} clinics, "
            f"{spec} specialties)"
        )

    data_parts.append("\nAll Regions (by facility count, ascending):")
    for region in analysis['all_regions']:
        data_parts.append(
            f"  - {region['region']}: {region['total_facilities']} facilities"
        )

    data_context = "\n".join(data_parts)

    # ---- Build conversation context for follow-ups ----
    conversation_context = ""
    if len(messages) > 1:
        prev_msgs = messages[-4:-1]
        if prev_msgs:
            ctx = []
            for m in prev_msgs:
                role = "User" if isinstance(m, HumanMessage) else "Assistant"
                ctx.append(f"{role}: {m.content[:300]}")
            conversation_context = "\n\nPrevious conversation:\n" + "\n".join(ctx)

    # ---- LLM generates the response ----
    system_prompt = """You are the CareConnect Medical Desert Analyzer, an expert on healthcare distribution in Ghana.
You have access to real data about healthcare facilities across all regions.

Your role:
- Analyze healthcare distribution data and identify underserved areas (medical deserts)
- Provide clear, actionable insights about regional healthcare gaps
- Compare regions and highlight disparities
- Suggest which regions need the most attention
- Use the actual data provided — never fabricate statistics

Formatting:
- Use markdown for readability
- Include relevant numbers and percentages
- Highlight critical findings with bold text
- Be professional but accessible"""

    user_prompt = (
        f"User Query: {user_query}"
        f"{conversation_context}\n\n"
        f"=== HEALTHCARE DATA ===\n{data_context}\n"
        "=======================\n\n"
        "Based on this real data, provide a helpful and insightful answer to the user's question."
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        response_text = response.content
    except Exception:
        # Fallback to a structured template if the LLM call fails
        response_text = _fallback_template(analysis, region_filter)

    # Store output for multi-agent coordination
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_outputs["medical_desert"] = response_text

    return {
        "messages": [AIMessage(content=response_text)],
        "current_agent": "medical_desert",
        "medical_desert_data": analysis,
        "agent_outputs": agent_outputs
    }


# ---------------------------------------------------------------------------
# Fallback template (used only when LLM is unavailable)
# ---------------------------------------------------------------------------

def _fallback_template(analysis: Dict, region_filter: str | None = None) -> str:
    """Generate a basic template response when the LLM is unavailable."""
    parts = [
        "**Medical Desert Analysis for Ghana**\n",
        f"Total Regions Analyzed: {analysis['total_regions']}",
        f"Total Healthcare Facilities: {analysis['total_facilities']}",
        f"Average Facilities per Region: {analysis['average_per_region']:.1f}\n",
    ]

    if analysis['medical_deserts']:
        parts.append(
            f"**Medical Deserts Identified: {len(analysis['medical_deserts'])} regions**"
        )
        parts.append(
            f"(Regions with < {analysis['desert_threshold']:.0f} facilities)\n"
        )
        for desert in analysis['medical_deserts'][:5]:
            parts.append(
                f"- **{desert['region']}**: {desert['total_facilities']} facilities "
                f"({desert['hospitals']} hospitals, {desert['clinics']} clinics)"
            )
    else:
        parts.append("No critical medical deserts identified.")

    parts.append("\n**Best Served Regions:**")
    for region in analysis['best_served']:
        parts.append(f"- {region['region']}: {region['total_facilities']} facilities")

    return "\n".join(parts)
