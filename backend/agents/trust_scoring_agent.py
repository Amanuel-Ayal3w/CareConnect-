"""
Trust Scoring Agent
Calculates trust scores for healthcare facilities based on data quality.
Uses LLM for facility name extraction AND contextual response generation.
"""

import json
from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Initialize LLM (used for extraction AND response generation)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def calculate_trust_score(facility: Dict) -> Dict:
    """
    Calculate comprehensive trust score (0-100) for a facility.

    Scoring breakdown:
    - Data Completeness (0-25): Contact info, address, description
    - Claim Consistency (0-25): Capacity, specialties, equipment alignment
    - External Validation (0-25): Website, social media, year established
    - Anomaly Detection (0-25): Suspicious data patterns
    """
    score = 0
    breakdown = {}
    flags = []

    # 1. Data Completeness (0-25 points)
    completeness = 0
    if facility.get('phone_numbers'):
        completeness += 8
    if facility.get('email'):
        completeness += 5
    if facility.get('address_line1') and facility.get('address_city'):
        completeness += 7
    if facility.get('description'):
        completeness += 5
    breakdown['completeness'] = completeness
    score += completeness

    # 2. Claim Consistency (0-25 points)
    consistency = 25  # Start with full points, deduct for inconsistencies

    capacity = facility.get('capacity', 0)
    facility_type = (facility.get('facility_type_id') or '').lower()

    if capacity:
        if 'hospital' in facility_type and capacity < 10:
            consistency -= 5
            flags.append("Low capacity for hospital")
        elif 'clinic' in facility_type and capacity > 100:
            consistency -= 3
            flags.append("High capacity for clinic")

    specialties = facility.get('specialties') or []
    if isinstance(specialties, list) and len(specialties) > 15:
        consistency -= 5
        flags.append("Unusually high number of specialties")

    breakdown['consistency'] = max(0, consistency)
    score += max(0, consistency)

    # 3. External Validation (0-25 points)
    validation = 0
    if facility.get('official_website'):
        validation += 10
    if facility.get('facebook_link') or facility.get('twitter_link'):
        validation += 5
    if facility.get('year_established'):
        year = facility.get('year_established')
        if 1900 <= year <= 2025:
            validation += 10
        else:
            flags.append(f"Suspicious establishment year: {year}")
    breakdown['validation'] = validation
    score += validation

    # 4. Anomaly Detection (0-25 points)
    anomaly_score = 25

    if not facility.get('name'):
        anomaly_score -= 10
        flags.append("Missing facility name")

    if not facility.get('address_city') and not facility.get('address_state_or_region'):
        anomaly_score -= 8
        flags.append("Missing location information")

    name = facility.get('name', '').lower()
    if 'test' in name or 'placeholder' in name or 'example' in name:
        anomaly_score -= 15
        flags.append("Suspicious facility name")

    breakdown['anomaly_check'] = max(0, anomaly_score)
    score += max(0, anomaly_score)

    # Generate recommendation label
    if score >= 80:
        recommendation = "Highly Trustworthy - Excellent data quality"
    elif score >= 60:
        recommendation = "Trustworthy - Good data quality"
    elif score >= 40:
        recommendation = "Moderate - Some data quality concerns"
    else:
        recommendation = "Low Trust - Significant data quality issues"

    return {
        'facility_id': facility.get('id'),
        'facility_name': facility.get('name'),
        'trust_score': score,
        'breakdown': breakdown,
        'flags': flags,
        'recommendation': recommendation
    }


def trust_scoring_agent(state: Dict) -> Dict:
    """
    Trust scoring agent node.
    1) Uses LLM to extract the facility name from conversation context.
    2) Calculates a trust score using structured rules.
    3) Uses LLM again to produce a contextual, natural-language analysis.
    Stores its output in agent_outputs for cross-agent coordination.
    """
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import os
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

    messages = state["messages"]
    last_message = messages[-1].content

    # ---- Step 1: Extract facility name via LLM ----
    conversation_context = ""
    if len(messages) > 1:
        prev_msgs = messages[-6:-1]
        if prev_msgs:
            ctx_parts = []
            for m in prev_msgs:
                role = "User" if isinstance(m, HumanMessage) else "Assistant"
                ctx_parts.append(f"{role}: {m.content[:300]}")
            conversation_context = "\n".join(ctx_parts)

    extraction_prompt = f"""Identify the healthcare facility name the user is asking about.

User Query: "{last_message}"

Previous conversation:
{conversation_context}

INSTRUCTIONS:
- If the user names a facility (e.g., "Trust score for Korle Bu"), extract "Korle Bu".
- If the user refers to a previous facility (e.g., "What is its score?", "Is the first one good?"), identify the most likely facility from the conversation context.
- If the user mentions multiple facilities, extract the most relevant one.
- If no specific facility can be identified, return "NONE".
- Return ONLY the facility name, nothing else."""

    try:
        facility_name = llm.invoke([
            SystemMessage(content="You are a precise entity extraction assistant. Extract exactly the facility name requested."),
            HumanMessage(content=extraction_prompt)
        ]).content.strip()
    except Exception:
        facility_name = "NONE"

    if facility_name == "NONE" or not facility_name:
        facility_name = state.get('facility_filter')

        if not facility_name or facility_name == "NONE":
            agent_outputs = state.get("agent_outputs") or {}
            if "recommendation" in agent_outputs:
                response_text = (
                    "I'd be happy to score a facility's trustworthiness. "
                    "Could you specify which facility you'd like me to verify? "
                    "You can name one from the recommendations above."
                )
            else:
                response_text = (
                    "Please specify which facility you'd like me to verify. "
                    "For example: 'What's the trust score for Korle Bu Teaching Hospital?'"
                )

            agent_outputs = dict(state.get("agent_outputs") or {})
            agent_outputs["trust_scoring"] = response_text

            return {
                "messages": [AIMessage(content=response_text)],
                "current_agent": "trust_scoring",
                "agent_outputs": agent_outputs
            }

    # ---- Step 2: Fetch facility from database ----
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT *
        FROM facilities
        WHERE name ILIKE %s
        LIMIT 1
    """, (f"%{facility_name}%",))

    facility = cursor.fetchone()
    cursor.close()
    conn.close()

    if not facility:
        response_text = f"I couldn't find a facility matching '{facility_name}'. Please check the name and try again."
        agent_outputs = dict(state.get("agent_outputs") or {})
        agent_outputs["trust_scoring"] = response_text
        return {
            "messages": [AIMessage(content=response_text)],
            "current_agent": "trust_scoring",
            "agent_outputs": agent_outputs
        }

    # ---- Step 3: Calculate trust score ----
    trust_result = calculate_trust_score(dict(facility))

    # ---- Step 4: LLM generates a contextual trust analysis ----
    trust_data = json.dumps({
        "facility_name": trust_result['facility_name'],
        "trust_score": trust_result['trust_score'],
        "max_score": 100,
        "breakdown": trust_result['breakdown'],
        "flags": trust_result['flags'],
        "recommendation": trust_result['recommendation'],
        "facility_type": facility.get('facility_type_id'),
        "location": f"{facility.get('address_city', '')}, {facility.get('address_state_or_region', '')}",
        "has_website": bool(facility.get('official_website')),
        "has_phone": bool(facility.get('phone_numbers')),
        "has_email": bool(facility.get('email')),
        "capacity": facility.get('capacity'),
        "specialties_count": len(facility.get('specialties') or [])
    }, indent=2)

    analysis_prompt = f"""You are the CareConnect Trust Scoring analyst. You've calculated a trust score for a healthcare facility.
Generate a clear, professional trust analysis response.

Trust Score Data:
{trust_data}

User Query: {last_message}

Guidelines:
- Present the trust score prominently (e.g., **72/100**)
- Explain what each breakdown category means in plain language
- If there are flags, explain what they mean and their potential impact
- Provide actionable advice (e.g., "verify contact info independently", "check for an updated website")
- Use markdown formatting for readability
- Be honest about data limitations
- If score is low, don't be alarmist — explain what might be missing vs what's genuinely concerning"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a healthcare data quality analyst providing trust assessments."),
            HumanMessage(content=analysis_prompt)
        ])
        response_text = response.content
    except Exception:
        # Fallback to template if LLM fails
        response_text = _fallback_template(trust_result)

    # Store output for multi-agent coordination
    agent_outputs = dict(state.get("agent_outputs") or {})
    agent_outputs["trust_scoring"] = response_text

    return {
        "messages": [AIMessage(content=response_text)],
        "current_agent": "trust_scoring",
        "trust_scores": trust_result,
        "agent_outputs": agent_outputs
    }


# ---------------------------------------------------------------------------
# Fallback template (used only when LLM is unavailable)
# ---------------------------------------------------------------------------

def _fallback_template(trust_result: Dict) -> str:
    """Generate a basic template response when the LLM is unavailable."""
    parts = [
        f"**Trust Score Analysis for {trust_result['facility_name']}**\n",
        f"Overall Trust Score: **{trust_result['trust_score']}/100**",
        f"Assessment: {trust_result['recommendation']}\n",
        "\n**Score Breakdown:**",
        f"- Data Completeness: {trust_result['breakdown']['completeness']}/25",
        f"- Claim Consistency: {trust_result['breakdown']['consistency']}/25",
        f"- External Validation: {trust_result['breakdown']['validation']}/25",
        f"- Anomaly Check: {trust_result['breakdown']['anomaly_check']}/25"
    ]

    if trust_result['flags']:
        parts.append("\n**Flags:**")
        for flag in trust_result['flags']:
            parts.append(f"- {flag}")
    else:
        parts.append("\nNo data quality issues detected.")

    return '\n'.join(parts)
