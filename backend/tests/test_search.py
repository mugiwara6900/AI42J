import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db
from app.services.search_service import search_service


def print_results(query: str, results: list):
    """
    Print search results in a formatted way
    
    Args:
        query: The search query
        results: List of search results
    """
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        section = result['section_number'] if result['section_number'] else "N/A"
        page = result['page_number'] if result['page_number'] else "N/A"
        distance = result['distance']
        content = result['content']
        
        # Show first 200 characters of content
        content_preview = content[:200] + "..." if len(content) > 200 else content
        
        print(f"\n[Result {i}]")
        print(f"Section Number: {section}")
        print(f"Page Number: {page}")
        print(f"Distance Score: {distance:.4f}")
        print(f"Content Preview:")
        print(f"  {content_preview}")
        print("-" * 80)


def test_search_queries():
    """Test the search service with predefined queries"""
    
    print("\n" + "=" * 80)
    print("LEGAL DOCUMENT SEARCH TEST")
    print("=" * 80)
    
    # Connect to database
    try:
        db.connect()
        print("✓ Database connection established")
    except Exception as e:
        print(f"✗ Error connecting to database: {e}")
        return
    
    # Test queries
    test_queries = [
        "What is the security deposit limit?",
        "Can a landlord enter my house without notice?",
        "How to terminate the tenancy agreement?"
    ]
    
    # Run each test query
    for query in test_queries:
        try:
            results = search_service.search_legal_docs(query, limit=3)
            print_results(query, results)
        except Exception as e:
            print(f"\n✗ Error searching for '{query}': {e}")
    
    # Disconnect from database
    db.disconnect()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


def test_single_query(query: str, limit: int = 3):
    """
    Test a single custom query
    
    Args:
        query: The search query
        limit: Number of results to return
    """
    try:
        db.connect()
        results = search_service.search_legal_docs(query, limit=limit)
        print_results(query, results)
        db.disconnect()
    except Exception as e:
        print(f"✗ Error: {e}")
        db.disconnect()


if __name__ == "__main__":
    # Run the predefined test queries
    test_search_queries()
    
    # Uncomment below to test a custom query
    # test_single_query("What are the rights of a tenant?", limit=5)
