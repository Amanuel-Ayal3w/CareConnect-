"""
Map visualization component using Folium
Creates interactive Ghana map with facility markers and medical desert overlay
"""

import folium
from folium.plugins import MarkerCluster
import pandas as pd


def create_ghana_map(facilities_df, regional_stats=None):
    """
    Create interactive map of Ghana with facility markers
    
    Args:
        facilities_df: DataFrame with facility locations
        regional_stats: Optional dict with regional statistics
    
    Returns:
        folium.Map object
    """
    
    # Ghana center coordinates
    ghana_center = [7.9465, -1.0232]
    
    # Create base map
    m = folium.Map(
        location=ghana_center,
        zoom_start=7,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add marker clusters for better performance
    marker_cluster = MarkerCluster(name="Facilities").add_to(m)
    
    # Add facility markers
    for idx, facility in facilities_df.iterrows():
        if pd.notna(facility['latitude']) and pd.notna(facility['longitude']):
            # Determine marker color based on facility type
            facility_type = str(facility.get('facility_type_id', '')).lower()
            
            if 'hospital' in facility_type:
                color = 'red'
                icon = 'plus-sign'
            elif 'clinic' in facility_type:
                color = 'blue'
                icon = 'heart'
            elif facility.get('organization_type') == 'ngo':
                color = 'green'
                icon = 'home'
            else:
                color = 'gray'
                icon = 'info-sign'
            
            # Create popup content
            popup_html = f"""
            <div style="width: 250px;">
                <h4>{facility['name']}</h4>
                <p><b>Type:</b> {facility.get('facility_type_id', 'N/A')}</p>
                <p><b>Location:</b> {facility.get('address_city', 'N/A')}, {facility.get('address_state_or_region', 'N/A')}</p>
            """
            
            specialties = facility.get('specialties')
            if isinstance(specialties, list) and specialties:
                popup_html += f"<p><b>Specialties:</b> {', '.join(specialties[:3])}</p>"
            
            phone_numbers = facility.get('phone_numbers')
            if isinstance(phone_numbers, list) and phone_numbers:
                popup_html += f"<p><b>Phone:</b> {phone_numbers[0]}</p>"
            
            if pd.notna(facility.get('capacity')):
                popup_html += f"<p><b>Capacity:</b> {facility['capacity']} beds</p>"
            
            popup_html += "</div>"
            
            # Add marker
            folium.Marker(
                location=[facility['latitude'], facility['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=facility['name'],
                icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
            ).add_to(marker_cluster)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; height: 140px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <p style="margin: 5px; font-weight: bold;">Facility Types</p>
        <p style="margin: 5px;"><i class="glyphicon glyphicon-plus-sign" style="color:red"></i> Hospital</p>
        <p style="margin: 5px;"><i class="glyphicon glyphicon-heart" style="color:blue"></i> Clinic</p>
        <p style="margin: 5px;"><i class="glyphicon glyphicon-home" style="color:green"></i> NGO</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m


def create_medical_desert_map(regional_stats_df):
    """
    Create choropleth map showing medical deserts
    
    Args:
        regional_stats_df: DataFrame with region, facility_count, is_desert
    
    Returns:
        folium.Map object
    """
    
    ghana_center = [7.9465, -1.0232]
    
    m = folium.Map(
        location=ghana_center,
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Note: Would need Ghana GeoJSON for proper choropleth
    # For now, add circle markers for each region center
    
    # Add region markers colored by desert status
    for idx, region in regional_stats_df.iterrows():
        # Skip unknown regions
        if region['region'] == 'Unknown':
            continue
            
        # Determine color
        if region['is_desert']:
            color = 'red'
            fill_color = 'red'
        elif region['facility_count'] < regional_stats_df['facility_count'].mean():
            color = 'orange'
            fill_color = 'orange'
        else:
            color = 'green'
            fill_color = 'green'
        
        # Create popup
        popup_text = f"""
        <b>{region['region']}</b><br>
        Facilities: {region['facility_count']}<br>
        Status: {'Medical Desert' if region['is_desert'] else 'Adequately Served'}
        """
        
        # Note: Would need actual region coordinates
        # This is a placeholder - in production, geocode region names
        
    return m
