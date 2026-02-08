"""
Populate Demo Coordinates for Large Scale Map Test
Distributes facilities without coordinates across major Ghanaian cities
to simulate a fully populated dataset for demonstration purposes.
"""

import sys
import os
import random
import psycopg2

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_postgres_connection

# Major cities center points (lat, lng)
CITIES = {
    "Accra": (5.6037, -0.1870, 0.15),  # City, Lat, Lng, Spread (degrees approx 15km)
    "Kumasi": (6.6885, -1.6244, 0.10),
    "Tamale": (9.4075, -0.8534, 0.08),
    "Takoradi": (4.8845, -1.7554, 0.05),
    "Cape Coast": (5.1315, -1.2795, 0.04),
    "Sunyani": (7.3349, -2.3123, 0.04),
    "Ho": (6.6124, 0.4696, 0.04),
    "Koforidua": (6.0784, -0.2714, 0.04),
    "Wa": (10.0601, -2.5099, 0.03),
    "Bolgatanga": (10.7856, -0.8514, 0.03)
}

# Distribution weights (more facilities in larger cities)
CITY_WEIGHTS = [0.45, 0.25, 0.08, 0.05, 0.05, 0.03, 0.03, 0.03, 0.015, 0.015]

def generate_random_coords(center_lat, center_lng, spread):
    """Generate random coordinates within a box around center"""
    lat_offset = random.uniform(-spread, spread)
    lng_offset = random.uniform(-spread, spread)
    return center_lat + lat_offset, center_lng + lng_offset

def populate_coordinates():
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # Get all facilities with missing coordinates
    cursor.execute("SELECT id, name, address_city FROM facilities WHERE latitude IS NULL")
    facilities = cursor.fetchall()
    
    print(f"Found {len(facilities)} facilities without coordinates.")
    
    updated_count = 0
    cities_list = list(CITIES.keys())
    
    for facility_id, name, city in facilities:
        # Try to match city from valid list, otherwise pick random weighted city
        target_city = None
        
        # Simple name matching for city
        if city:
            for c in cities_list:
                if c.lower() in city.lower():
                    target_city = c
                    break
        
        # If no city match, assign to random major city based on weights
        if not target_city:
            target_city = random.choices(cities_list, weights=CITY_WEIGHTS, k=1)[0]
            
        # Generate coords
        base_lat, base_lng, spread = CITIES[target_city]
        new_lat, new_lng = generate_random_coords(base_lat, base_lng, spread)
        
        # Update facility
        cursor.execute("""
            UPDATE facilities 
            SET latitude = %s, longitude = %s, address_city = COALESCE(address_city, %s)
            WHERE id = %s
        """, (new_lat, new_lng, target_city, facility_id))
        
        updated_count += 1
        
        if updated_count % 50 == 0:
            print(f"Processed {updated_count} facilities...")
            conn.commit()
            
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ Successfully populated {updated_count} facilities with demo coordinates!")
    print("Refresh the Streamlit Map to see the results.")

if __name__ == "__main__":
    populate_coordinates()
