"""
Facility Search Page
Search and filter healthcare facilities
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd

from frontend.components.data_loader import load_facilities, calculate_trust_score_simple

# Page config
st.set_page_config(page_title="Search Facilities", page_icon="🔍", layout="wide")

st.title("🔍 Search Healthcare Facilities")
st.markdown("Find and filter healthcare facilities across Ghana")

# Load data
facilities_df = load_facilities()

# Search and filter section
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "🔎 Search facilities",
        placeholder="e.g., hospital, pediatric, eye care...",
        help="Search by name, specialty, or description"
    )

with col2:
    city_options = ["All"] + sorted(facilities_df['address_city'].dropna().unique().tolist())
    selected_city = st.selectbox("📍 City", city_options)

with col3:
    type_options = ["All", "hospital", "clinic"]
    selected_type = st.selectbox("🏥 Type", type_options)

# Advanced filters in expander
with st.expander("🎛️ Advanced Filters"):
    col1, col2 = st.columns(2)
    
    with col1:
        region_options = ["All"] + sorted(facilities_df['address_state_or_region'].dropna().unique().tolist())
        selected_region = st.selectbox("Region", region_options)
    
    with col2:
        show_with_phone = st.checkbox("Only facilities with phone numbers")

# Apply filters
filtered_df = facilities_df.copy()

# Text search
if search_query:
    search_mask = (
        filtered_df['name'].str.contains(search_query, case=False, na=False) |
        filtered_df['description'].str.contains(search_query, case=False, na=False)
    )
    filtered_df = filtered_df[search_mask]

# City filter
if selected_city != "All":
    filtered_df = filtered_df[filtered_df['address_city'] == selected_city]

# Type filter
if selected_type != "All":
    filtered_df = filtered_df[filtered_df['facility_type_id'] == selected_type]

# Region filter
if selected_region != "All":
    filtered_df = filtered_df[filtered_df['address_state_or_region'] == selected_region]

# Phone filter
if show_with_phone:
    filtered_df = filtered_df[filtered_df['phone_numbers'].notna()]

# Display results count
st.markdown(f"### Found {len(filtered_df)} facilities")

# Sort options
sort_by = st.selectbox(
    "Sort by",
    ["Name (A-Z)", "Name (Z-A)", "City"]
)

if sort_by == "Name (A-Z)":
    filtered_df = filtered_df.sort_values('name')
elif sort_by == "Name (Z-A)":
    filtered_df = filtered_df.sort_values('name', ascending=False)
elif sort_by == "City":
    filtered_df = filtered_df.sort_values('address_city')

# Display results
if len(filtered_df) > 0:
    for idx, facility in filtered_df.iterrows():
        with st.expander(f"**{facility['name']}** - {facility.get('address_city', 'Unknown')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Basic info
                facility_type = facility.get('facility_type_id') or 'N/A'
                st.markdown(f"**Type:** {facility_type.title()}")
                st.markdown(f"**Location:** {facility.get('address_city', 'N/A')}, {facility.get('address_state_or_region', 'N/A')}")
                
                # Specialties
                # Specialties
                specialties = facility.get('specialties')
                if isinstance(specialties, list) and specialties:
                    st.markdown(f"**Specialties:** {', '.join(specialties[:5])}")
                
                # Contact
                phones = facility.get('phone_numbers')
                if isinstance(phones, list) and phones:
                    st.markdown(f"**Phone:** {', '.join(phones[:2])}")
                
                if pd.notna(facility.get('email')):
                    st.markdown(f"**Email:** {facility['email']}")
                
                if pd.notna(facility.get('official_website')):
                    st.markdown(f"**Website:** [{facility['official_website']}]({facility['official_website']})")
                
                # Description
                if pd.notna(facility.get('description')):
                    st.markdown(f"**About:** {facility['description'][:200]}...")
            
            with col2:
                # Trust score
                trust_score = calculate_trust_score_simple(facility)
                
                if trust_score >= 80:
                    color = "green"
                    status = "Highly Trustworthy"
                elif trust_score >= 60:
                    color = "blue"
                    status = "Trustworthy"
                elif trust_score >= 40:
                    color = "orange"
                    status = "Moderate"
                else:
                    color = "red"
                    status = "Low Trust"
                
                st.metric("Trust Score", f"{trust_score}/100")
                st.markdown(f":{color}[{status}]")
                
                # Additional info
                if pd.notna(facility.get('capacity')):
                    st.metric("Capacity", f"{facility['capacity']} beds")
                
                if pd.notna(facility.get('year_established')):
                    st.metric("Established", facility['year_established'])
    
    # Export option
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    
    export_df = filtered_df[[
        'name', 'facility_type_id', 'address_city', 
        'address_state_or_region', 'phone_numbers', 'email'
    ]].copy()
    
    export_df.columns = ['Name', 'Type', 'City', 'Region', 'Phone', 'Email']
    
    # Format phone numbers for CSV
    export_df['Phone'] = export_df['Phone'].apply(
        lambda x: ', '.join(x) if isinstance(x, list) else ''
    )
    
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name=f"careconnect_search_results.csv",
        mime="text/csv"
    )

else:
    st.info("No facilities found. Try adjusting your search criteria.")

# Footer
st.markdown("---")
st.caption("💡 Tip: Use the search box for semantic search across facility names and descriptions")
