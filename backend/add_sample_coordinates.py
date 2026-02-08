"""
Add sample coordinates to major Accra facilities for map testing
This adds lat/long for well-known facilities so the map can display markers
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_postgres_connection

# Sample coordinates for major Accra facilities (verified from Google Maps)
sample_coordinates = [
    # Major hospitals in Accra with known locations
    ("Korle Bu Teaching Hospital", 5.5389, -0.2270),
    ("37 Military Hospital", 5.5823, -0.1821),
    ("Ridge Hospital", 5.5736, -0.1969),
    ("Achimota Hospital", 5.6128, -0.2142),
    ("La General Hospital", 5.5947, -0.1687),
    ("University of Ghana Medical Centre", 5.6512, -0.1843),
    ("Tema General Hospital", 5.6698, -0.0166),
    ("Legon Hospital", 5.6485, -0.1877),
    ("Lister Hospital", 5.5892, -0.2086),
    ("Nyaho Medical Centre", 5.6247, -0.1753),
]

def add_sample_coordinates():
    """Add coordinates to facilities by matching names"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    
    for facility_name, lat, lng in sample_coordinates:
        # Find facility by name (case-insensitive partial match)
        cursor.execute("""
            UPDATE facilities 
            SET latitude = %s, longitude = %s
            WHERE LOWER(name) LIKE LOWER(%s)
            AND latitude IS NULL
        """, (lat, lng, f"%{facility_name}%"))
        
        count = cursor.rowcount
        updated_count += count
        
        if count > 0:
            print(f"✓ Updated {count} facility(ies) matching '{facility_name}'")
        else:
            print(f"  No match found for '{facility_name}'")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Total facilities updated: {updated_count}")
    return updated_count

if __name__ == "__main__":
    print("Adding sample coordinates to Accra facilities...\n")
    count = add_sample_coordinates()
    
    if count > 0:
        print(f"\n🗺️  Map should now show {count} facilities in Accra!")
        print("Refresh your Streamlit app to see the markers.")
    else:
        print("\n⚠️  Warning: No facilities were updated. Check facility names in database.")
