"""
CareConnect Ghana - Main Streamlit App
Healthcare facility mapping and medical desert analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="CareConnect Ghana",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🏥 CareConnect Ghana</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered healthcare facility mapping and medical desert analysis</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=CareConnect", width="stretch")
    
    st.markdown("---")
    
    st.header("Quick Stats")
    
    # Load basic stats
    try:
        from frontend.components.data_loader import load_facilities, load_regional_statistics
        
        facilities_df = load_facilities()
        regional_stats = load_regional_statistics()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Total Facilities", 
                len(facilities_df),
                help="Healthcare facilities with location data"
            )
        with col2:
            st.metric(
                "Regions", 
                regional_stats['total_regions'],
                help="Administrative regions analyzed"
            )
        
        # Medical deserts metric with delta
        desert_count = len(regional_stats['medical_deserts'])
        desert_pct = (desert_count / regional_stats['total_regions']) * 100
        
        st.metric(
            "Medical Deserts",
            desert_count,
            f"-{desert_pct:.0f}% of regions",
            delta_color="inverse",
            help="Regions with below-average facility coverage"
        )
        
        # Average facilities per region
        st.metric(
            "Avg Facilities/Region",
            f"{regional_stats['average_per_region']:.1f}",
            help="Mean number of facilities per region"
        )
        
    except Exception as e:
        st.error(f"Could not load statistics: {str(e)}")
    
    st.markdown("---")
    
    st.markdown("""
    ### 📖 About
    
    CareConnect transforms messy healthcare data into trusted, region-level decisions 
    that help NGOs and governments identify medical deserts and act faster.
    
    **Features:**
    - 🗺️ Interactive facility map
    - 🤖 AI agent assistance
    - 📊 Medical desert analysis
    - 🔍 Facility search & filtering
    """)
    
    st.markdown("---")
    st.caption("Powered by LangGraph & RAG")

# Main content
st.markdown("## Welcome to CareConnect")

st.info("💡 **Tip:** Navigate to the AI Agent page to ask questions about healthcare facilities. The chat input is at the bottom of the page!")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🗺️ Interactive Map
    Visualize healthcare facilities across Ghana with:
    - Facility locations and details
    - Medical desert regions
    - Filterable by type and specialty
    """)
    if st.button("📍 Open Map", width="stretch"):
        st.switch_page("pages/1_🗺️_Map.py")

with col2:
    st.markdown("""
    ### 🤖 AI Agent
    Ask questions about healthcare:
    - Find facilities in your area
    - Identify medical deserts
    - Verify facility trustworthiness
    """)
    if st.button("💬 Chat with Agent", width="stretch"):
        st.switch_page("pages/2_🤖_Agent.py")

with col3:
    st.markdown("""
    ### 🔍 Search Facilities
    Find healthcare providers:
    - Filter by location & type
    - View trust scores
    - Get contact information
    """)
    if st.button("🔎 Search Now", width="stretch"):
        st.switch_page("pages/3_🔍_Search.py")

# Quick insights
st.markdown("---")
st.markdown("## 📈 Quick Insights")

try:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Top Regions")
        for region in regional_stats['best_served'][:3]:
            st.write(f"**{region['region']}**: {region['total_facilities']} facilities")
    
    with col2:
        st.markdown("### Medical Deserts")
        for region in regional_stats['medical_deserts'][:3]:
            st.write(f"⚠️ **{region['region']}**: {region['total_facilities']} facilities")
    
    with col3:
        st.markdown("### Facility Types")
        hospitals = len(facilities_df[facilities_df['facility_type_id'] == 'hospital'])
        clinics = len(facilities_df[facilities_df['facility_type_id'] == 'clinic'])
        st.write(f"**Hospitals**: {hospitals}")
        st.write(f"**Clinics**: {clinics}")
        st.write(f"**Other**: {len(facilities_df) - hospitals - clinics}")

except Exception as e:
    st.info("Loading insights...")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>CareConnect Ghana | Transforming Healthcare Data into Action</p>
    <p><small>Data powered by AI analysis | Last updated: 2024</small></p>
</div>
""", unsafe_allow_html=True)
