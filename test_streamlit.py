"""
Test script to verify Streamlit app can load data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing CareConnect Streamlit components...")

try:
    print("\n1. Testing data loader...")
    from frontend.components.data_loader import load_facilities, load_regional_statistics
    
    facilities = load_facilities()
    print(f"   ✓ Loaded {len(facilities)} facilities")
    
    stats = load_regional_statistics()
    print(f"   ✓ Loaded stats for {stats['total_regions']} regions")
    print(f"   ✓ Identified {len(stats['medical_deserts'])} medical deserts")
    
    print("\n2. Testing map visualization...")
    from frontend.components.map_viz import create_ghana_map
    
    ghana_map = create_ghana_map(facilities.head(10))  # Test with 10 facilities
    print(f"   ✓ Map created successfully")
    
    print("\n3. Testing agent integration...")
    from backend.agents.graph import invoke_agent
    
    test_response = invoke_agent("Find hospitals in Accra", thread_id="test_frontend")
    print(f"   ✓ Agent responded: {test_response[:100]}...")
    
    print("\n✅ All components loaded successfully!")
    print("\nYou can now run the Streamlit app with:")
    print("   uv run streamlit run frontend/app.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
