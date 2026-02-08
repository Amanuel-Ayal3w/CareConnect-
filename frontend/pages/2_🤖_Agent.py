"""
AI Agent Chat Interface
Interactive chat with CareConnect healthcare AI agent
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from backend.agents.graph import invoke_agent

# Page config
st.set_page_config(page_title="AI Agent", page_icon="🤖", layout="wide")

st.title("🤖 CareConnect AI Agent")
st.markdown("Ask questions about healthcare facilities, medical deserts, and facility trustworthiness")

# Initialize chat history
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
    # Add welcome message
    st.session_state.chat_messages.append({
        'role': 'assistant',
        'content': """Hello! I'm the CareConnect AI agent. I can help you with:

- 🗺️ **Finding healthcare facilities** - "Find pediatric hospitals in Accra"
- 📊 **Identifying medical deserts** - "Which regions are underserved?"
- ✅ **Verifying facility trustworthiness** - "What's the trust score for Hospital X?"

What would you like to know?"""
    })

# Initialize user ID for conversation persistence
if 'user_id' not in st.session_state:
    import uuid
    st.session_state.user_id = str(uuid.uuid4())

# Sidebar with example queries
with st.sidebar:
    st.header("💡 Example Questions")
    
    example_queries = [
        "Which regions in Ghana are medical deserts?",
        "Find eye hospitals in Accra",
        "What's the trust score for Korle Bu Teaching Hospital?",
        "Show me pediatric clinics in Kumasi",
        "Which regions need more healthcare facilities?"
    ]
    
    st.markdown("Click to try:")
    for query in example_queries:
        if st.button(query, key=f"example_{query}", width="stretch"):
            st.session_state.pending_query = query
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat History", width="stretch"):
        st.session_state.chat_messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### 🤖 Agent Capabilities
    
    **Medical Desert Analyzer**
    - Identifies underserved regions
    - Calculates facility density
    - Compares regional coverage
    
    **Trust Scoring**
    - Verifies facility claims
    - Calculates 0-100 trust scores
    - Flags data quality issues
    
    **Facility Recommendation**
    - Semantic search via RAG
    - Location-based filtering
    - Contact information
    """)

# Display chat messages
for message in st.session_state.chat_messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input (always visible)
prompt = st.chat_input("Ask me anything about healthcare in Ghana...")

# Handle pending query from example buttons
if hasattr(st.session_state, 'pending_query'):
    prompt = st.session_state.pending_query
    del st.session_state.pending_query
    # Rerun to process the pending query
    st.rerun()

# Process new message
if prompt:
    # Add user message to chat
    st.session_state.chat_messages.append({'role': 'user', 'content': prompt})
    
    # Get agent response
    with st.spinner("Thinking..."):
        try:
            response = invoke_agent(prompt, thread_id=st.session_state.user_id)
            
            # Add to chat history
            st.session_state.chat_messages.append({'role': 'assistant', 'content': response})
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            st.session_state.chat_messages.append({'role': 'assistant', 'content': error_msg})
    
    # Rerun to display new messages
    st.rerun()

# Footer
st.markdown("---")
st.caption("💬 Powered by LangGraph multi-agent system with GPT-4 and RAG")
