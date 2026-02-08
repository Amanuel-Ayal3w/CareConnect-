import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="CareConnect - Healthcare Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean, professional styling
st.markdown("""
<style>
    /* Main content area */
    .main {
        padding: 2rem;
    }
    
    /* Headers */
    h1 {
        color: #1f2937;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #374151;
        font-weight: 500;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #4b5563;
        font-weight: 500;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Cards */
    .stCard {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f9fafb;
        padding: 2rem 1rem;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8;
    }
    
    /* Remove extra spacing */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    
    /* Tables */
    .dataframe {
        border: 1px solid #e5e7eb !important;
        border-radius: 8px;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 6px;
        border-left: 4px solid #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load the facility and NGO data from CSV"""
    data_path = Path(__file__).parent / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
    df = pd.read_csv(data_path)
    return df

# Sidebar navigation
def sidebar():
    st.sidebar.title("CareConnect")
    st.sidebar.markdown("Healthcare Intelligence Platform")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Facility Search", "Map View", "Analytics"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    
    return page

# Dashboard page
def dashboard_page(df):
    st.title("Healthcare Overview")
    st.markdown("Comprehensive healthcare facility and NGO insights for Ghana")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    facilities_count = len(df[df['organization_type'] == 'facility'])
    ngos_count = len(df[df['organization_type'] == 'ngo'])
    total_orgs = len(df)
    cities_count = df['address_city'].nunique()
    
    with col1:
        st.metric("Total Organizations", f"{total_orgs:,}")
    
    with col2:
        st.metric("Healthcare Facilities", f"{facilities_count:,}")
    
    with col3:
        st.metric("NGOs", f"{ngos_count:,}")
    
    with col4:
        st.metric("Cities Covered", f"{cities_count:,}")
    
    st.markdown("---")
    
    # Facility types breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Facility Types Distribution")
        facility_types = df[df['organization_type'] == 'facility']['facilityTypeId'].value_counts()
        
        if not facility_types.empty:
            fig = px.pie(
                values=facility_types.values,
                names=facility_types.index,
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_layout(
                showlegend=True,
                height=350,
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No facility type data available")
    
    with col2:
        st.subheader("Operator Type Distribution")
        operator_types = df[df['organization_type'] == 'facility']['operatorTypeId'].value_counts()
        
        if not operator_types.empty:
            fig = px.bar(
                x=operator_types.index,
                y=operator_types.values,
                labels={'x': 'Operator Type', 'y': 'Count'},
                color=operator_types.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                showlegend=False,
                height=350,
                margin=dict(t=20, b=20, l=20, r=20),
                xaxis_title="",
                yaxis_title="Number of Facilities"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No operator type data available")
    
    # Recent additions
    st.subheader("Recent Organizations")
    recent_df = df[['name', 'organization_type', 'address_city', 'facilityTypeId']].head(10)
    recent_df.columns = ['Name', 'Type', 'City', 'Facility Type']
    st.dataframe(recent_df, use_container_width=True, hide_index=True)

# Facility search page
def search_page(df):
    st.title("Facility Search")
    st.markdown("Search and filter healthcare facilities and NGOs")
    
    # Search and filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search by name", placeholder="Enter facility or NGO name")
    
    with col2:
        org_type = st.selectbox(
            "Organization Type",
            ["All", "Facility", "NGO"]
        )
    
    with col3:
        cities = ["All"] + sorted(df['address_city'].dropna().unique().tolist())
        selected_city = st.selectbox("City", cities)
    
    # Filter data
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]
    
    if org_type != "All":
        filtered_df = filtered_df[filtered_df['organization_type'] == org_type.lower()]
    
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df['address_city'] == selected_city]
    
    # Display results
    st.markdown(f"### Results ({len(filtered_df)} organizations found)")
    
    if len(filtered_df) > 0:
        # Display columns
        display_cols = ['name', 'organization_type', 'address_city', 'address_stateOrRegion', 'facilityTypeId']
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        results_df = filtered_df[available_cols].copy()
        results_df.columns = [col.replace('_', ' ').title() for col in results_df.columns]
        
        st.dataframe(results_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="careconnect_search_results.csv",
            mime="text/csv"
        )
    else:
        st.info("No results found. Try adjusting your filters.")

# Map view page
def map_page(df):
    st.title("Geographic Distribution")
    st.markdown("Interactive map of healthcare facilities and NGOs")
    
    # For now, show a placeholder since we need geocoding
    st.info("Map visualization requires geocoding coordinates. This feature will display facility locations on an interactive map.")
    
    # City distribution table as alternative
    st.subheader("Organizations by City")
    city_counts = df.groupby('address_city').size().reset_index(name='Count')
    city_counts = city_counts.sort_values('Count', ascending=False).head(20)
    city_counts.columns = ['City', 'Number of Organizations']
    
    # Bar chart
    fig = px.bar(
        city_counts,
        x='City',
        y='Number of Organizations',
        color='Number of Organizations',
        color_continuous_scale='Blues'
    )
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.dataframe(city_counts, use_container_width=True, hide_index=True)

# Analytics page
def analytics_page(df):
    st.title("Healthcare Analytics")
    st.markdown("In-depth analysis of healthcare coverage and capabilities")
    
    # Specialties analysis
    st.subheader("Medical Specialties Coverage")
    
    # Parse specialties from JSON-like string format
    import json
    import ast
    
    specialties_list = []
    for spec_str in df['specialties'].dropna():
        try:
            # Try to parse as Python literal
            specs = ast.literal_eval(spec_str)
            if isinstance(specs, list):
                specialties_list.extend(specs)
        except:
            pass
    
    if specialties_list:
        specialty_counts = pd.Series(specialties_list).value_counts().head(15)
        
        fig = px.bar(
            x=specialty_counts.values,
            y=specialty_counts.index,
            orientation='h',
            labels={'x': 'Number of Facilities', 'y': 'Specialty'},
            color=specialty_counts.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=150)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Specialty data is being processed")
    
    st.markdown("---")
    
    # Regional coverage
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Organizations by Region")
        region_counts = df['address_stateOrRegion'].value_counts().head(10)
        
        if not region_counts.empty:
            fig = px.pie(
                values=region_counts.values,
                names=region_counts.index,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regional data available")
    
    with col2:
        st.subheader("Capacity Analysis")
        capacity_df = df[df['capacity'].notna()][['name', 'capacity', 'address_city']].sort_values('capacity', ascending=False).head(10)
        
        if not capacity_df.empty:
            capacity_df.columns = ['Facility', 'Bed Capacity', 'City']
            st.dataframe(capacity_df, use_container_width=True, hide_index=True)
        else:
            st.info("No capacity data available")

# Main app
def main():
    try:
        df = load_data()
        page = sidebar()
        
        if page == "Dashboard":
            dashboard_page(df)
        elif page == "Facility Search":
            search_page(df)
        elif page == "Map View":
            map_page(df)
        elif page == "Analytics":
            analytics_page(df)
    
    except FileNotFoundError:
        st.error("Data file not found. Please ensure 'Virtue Foundation Ghana v0.3 - Sheet1.csv' is in the project directory.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
