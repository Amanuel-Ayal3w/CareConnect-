"""
Interactive Map Page
Shows Ghana map with healthcare facilities and medical desert visualization
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd

from frontend.components.data_loader import load_facilities, get_facility_counts_by_region
from frontend.components.map_viz import create_ghana_map

# Page config
st.set_page_config(page_title="Healthcare Map", page_icon="🗺️", layout="wide")

st.title("🗺️ Ghana Healthcare Facility Map")
st.markdown("Interactive map showing healthcare facilities and medical desert regions")

# Filters in sidebar
with st.sidebar:
    st.header("🎛️ Map Filters")
    
    show_hospitals = st.checkbox(" Show Hospitals", value=True)
    show_clinics = st.checkbox(" Show Clinics", value=True)
    show_ngos = st.checkbox(" Show NGOs", value=True)
    
    st.markdown("---")
    
    # Region filter
    regions = ["All"] + sorted(load_facilities()['address_state_or_region'].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by Region", regions)
    
    st.markdown("---")
    
    # Map info
    st.markdown("""
    ### Legend
    - 🔴 **Red**: Hospitals
    - 🔵 **Blue**: Clinics
    - 🟢 **Green**: NGOs
    
    Click on markers for facility details!
    """)

# Load data
try:
    with st.spinner("Loading facility data..."):
        facilities_df = load_facilities()
        
        # Apply filters
        filtered_df = facilities_df.copy()
        
        # Filter by facility type
        type_filters = []
        if show_hospitals:
            type_filters.append('hospital')
        if show_clinics:
            type_filters.append('clinic')
        
        if type_filters:
            filtered_df = filtered_df[filtered_df['facility_type_id'].isin(type_filters)]
        
        # Filter by organization type (NGOs)
        if not show_ngos:
            filtered_df = filtered_df[filtered_df['organization_type'] != 'ngo']
        
        # Filter by region
        if selected_region != "All":
            filtered_df = filtered_df[filtered_df['address_state_or_region'] == selected_region]
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Facilities Shown", len(filtered_df))
        with col2:
            hospitals_count = len(filtered_df[filtered_df['facility_type_id'] == 'hospital'])
            st.metric("Hospitals", hospitals_count)
        with col3:
            clinics_count = len(filtered_df[filtered_df['facility_type_id'] == 'clinic'])
            st.metric("Clinics", clinics_count)
        with col4:
            ngos_count = len(filtered_df[filtered_df['organization_type'] == 'ngo'])
            st.metric("NGOs", ngos_count)
        
        st.markdown("---")
        
        # Create and display map
        if len(filtered_df) > 0:
            with st.spinner("Rendering map..."):
                ghana_map = create_ghana_map(filtered_df)
                
                # Display map
                map_data = st_folium(
                    ghana_map,
                    width="100%",
                    height=600,
                    returned_objects=[]
                )
            
            # Show facility details below map
            st.markdown("### 📋 Facility List")
            
            # Create display dataframe
            display_df = filtered_df[['name', 'facility_type_id', 'address_city', 'address_state_or_region', 'phone_numbers']].copy()
            display_df.columns = ['Name', 'Type', 'City', 'Region', 'Phone']
            
            # Format phone numbers
            display_df['Phone'] = display_df['Phone'].apply(
                lambda x: ', '.join(x[:2]) if isinstance(x, list) and x else ''
            )
            
            # Display with search
            search_term = st.text_input("🔍 Search facilities by name", placeholder="Type to filter...")
            
            if search_term:
                display_df = display_df[display_df['Name'].str.contains(search_term, case=False, na=False)]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Name": st.column_config.TextColumn("Facility Name", width="large"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "City": st.column_config.TextColumn("City", width="medium"),
                    "Region": st.column_config.TextColumn("Region", width="medium"),
                    "Phone": st.column_config.TextColumn("Contact", width="medium")
                }
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Facility List (CSV)",
                data=csv,
                file_name="ghana_healthcare_facilities.csv",
                mime="text/csv"
            )
            
        else:
            st.warning("No facilities match the selected filters. Try changing your filter settings.")
    
except Exception as e:
    st.error(f"Error loading map: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.caption("💡 Tip: Click on map markers to see detailed facility information")
