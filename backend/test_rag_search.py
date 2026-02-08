"""
Test RAG retrieval system with various queries
Validates semantic search, filtering, and result quality
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag_retrieval import (
    semantic_search,
    search_facilities_by_location,
    search_facilities_by_specialty,
    search_ngos_by_mission,
    format_search_results,
    facility_search_tool
)


def print_results(title: str, results: list):
    """Pretty print search results"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    
    formatted = format_search_results(results)
    
    if not formatted['results']:
        print("No results found")
        return
    
    for i, result in enumerate(formatted['results'], 1):
        print(f"\n{i}. {result['name']}")
        print(f"   Type: {result['type']} ({result.get('facility_type', 'N/A')})")
        print(f"   Score: {result['similarity_score']}")
        print(f"   Location: {result['location']['city']}, {result['location']['region']}")
        
        if result.get('specialties'):
            specialties = result['specialties'][:5]
            print(f"   Specialties: {', '.join(specialties)}")
        
        if result.get('capacity'):
            print(f"   Capacity: {result['capacity']} beds")
        
        if result.get('phone_numbers'):
            phones = result['phone_numbers'][:2]
            print(f"   Phone: {', '.join(phones)}")
        
        if result.get('description'):
            desc = result['description'][:150] + "..." if len(result.get('description', '')) > 150 else result.get('description', '')
            print(f"   Description: {desc}")


def test_basic_semantic_search():
    """Test 1: Basic semantic search"""
    print("\n🔍 TEST 1: Basic Semantic Search")
    results = semantic_search("hospitals with ICU in Accra", top_k=5)
    print_results("Query: 'hospitals with ICU in Accra'", results)


def test_location_filtering():
    """Test 2: Location-based filtering"""
    print("\n🔍 TEST 2: Location Filtering")
    results = search_facilities_by_location(
        query="maternity clinic",
        city="Kumasi",
        top_k=5
    )
    print_results("Query: 'maternity clinic' in Kumasi", results)


def test_specialty_search():
    """Test 3: Specialty-based search"""
    print("\n🔍 TEST 3: Specialty Search")
    results = search_facilities_by_specialty(
        specialty="ophthalmology",
        top_k=5
    )
    print_results("Query: Facilities with 'ophthalmology' specialty", results)


def test_eye_care():
    """Test 4: Eye care specialists"""
    print("\n🔍 TEST 4: Eye Care Specialists")
    results = semantic_search(
        query="eye care specialists and vision centers",
        entity_type="facility",
        top_k=5
    )
    print_results("Query: 'eye care specialists and vision centers'", results)


def test_dental_clinics():
    """Test 5: Dental clinics in Tema"""
    print("\n🔍 TEST 5: Dental Clinics")
    results = search_facilities_by_location(
        query="dental clinic dentist",
        city="Tema",
        top_k=5
    )
    print_results("Query: 'dental clinic' in Tema", results)


def test_ngo_search():
    """Test 6: NGO mission search"""
    print("\n🔍 TEST 6: NGO Mission Search")
    results = search_ngos_by_mission(
        query="HIV AIDS prevention treatment support",
        top_k=5
    )
    print_results("Query: NGOs working on 'HIV AIDS prevention'", results)


def test_regional_search():
    """Test 7: Regional search"""
    print("\n🔍 TEST 7: Regional Search")
    results = search_facilities_by_location(
        query="government hospital",
        region="Ashanti",
        top_k=5
    )
    print_results("Query: 'government hospital' in Ashanti Region", results)


def test_emergency_services():
    """Test 8: Emergency and trauma services"""
    print("\n🔍 TEST 9: Emergency Services")
    results = semantic_search(
        query="emergency room trauma center 24 hour care",
        entity_type="facility",
        top_k=5,
        min_similarity=0.4
    )
    print_results("Query: 'emergency room trauma center'", results)


def test_langraph_tool():
    """Test 9: LangGraph tool format"""
    print("\n🔍 TEST 9: LangGraph Tool Output")
    print("\n" + "="*70)
    print("Testing facility_search_tool() for LangGraph agents")
    print("="*70)
    
    output = facility_search_tool(
        query="hospitals with surgery department",
        location="Accra"
    )
    print("\nTool Output (formatted for agent):")
    print(output)


def test_minimum_similarity():
    """Test 10: Minimum similarity threshold"""
    print("\n🔍 TEST 10: Similarity Threshold")
    
    # High threshold - should return fewer but more relevant results
    results_high = semantic_search(
        query="pediatric children's hospital",
        entity_type="facility",
        top_k=10,
        min_similarity=0.6
    )
    
    print(f"\nWith min_similarity=0.6: {len(results_high)} results")
    if results_high:
        formatted = format_search_results(results_high)
        for r in formatted['results'][:3]:
            print(f"  - {r['name']} (score: {r['similarity_score']})")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("🧪 RAG RETRIEVAL SYSTEM - COMPREHENSIVE TESTS")
    print("="*70)
    
    tests = [
        test_basic_semantic_search,
        test_location_filtering,
        test_specialty_search,
        test_eye_care,
        test_dental_clinics,
        test_ngo_search,
        test_regional_search,
        test_emergency_services,
        test_langraph_tool,
        test_minimum_similarity
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Test failed: {test_func.__name__}")
            print(f"   Error: {e}")
    
    print("\n" + "="*70)
    print("✅ Test suite completed!")
    print("="*70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG retrieval system")
    parser.add_argument('--test', type=int, help='Run specific test number (1-10)')
    parser.add_argument('--query', type=str, help='Custom query to test')
    parser.add_argument('--city', type=str, help='Filter by city')
    
    args = parser.parse_args()
    
    if args.query:
        # Custom query
        print(f"\nCustom Query: '{args.query}'")
        filters = {'city': args.city} if args.city else None
        results = semantic_search(args.query, top_k=5, filters=filters)
        print_results(f"Custom Query: '{args.query}'", results)
    elif args.test:
        # Run specific test
        tests = {
            1: test_basic_semantic_search,
            2: test_location_filtering,
            3: test_specialty_search,
            4: test_eye_care,
            5: test_dental_clinics,
            6: test_ngo_search,
            7: test_regional_search,
            8: test_emergency_services,
            9: test_langraph_tool,
            10: test_minimum_similarity
        }
        if args.test in tests:
            tests[args.test]()
        else:
            print(f"Invalid test number. Choose 1-{len(tests)}")
    else:
        # Run all tests
        run_all_tests()
