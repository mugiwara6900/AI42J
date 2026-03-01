import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db


def test_database_connection():
    """Test if database connection works"""
    print("\n" + "=" * 80)
    print("TEST 1: Database Connection")
    print("=" * 80)
    
    try:
        db.connect()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_table_exists():
    """Test if the tenant_landlord_rights table exists"""
    print("\n" + "=" * 80)
    print("TEST 2: Table Existence")
    print("=" * 80)
    
    try:
        conn = db.get_connection()
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tenant_landlord_rights'
        )
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            
            if result['exists']:
                print("✓ Table 'tenant_landlord_rights' exists")
                return True
            else:
                print("✗ Table 'tenant_landlord_rights' does not exist")
                print("  Please create the table first")
                return False
                
    except Exception as e:
        print(f"✗ Error checking table existence: {e}")
        return False


def test_data_count():
    """Test and display the count of records in the table"""
    print("\n" + "=" * 80)
    print("TEST 3: Data Count")
    print("=" * 80)
    
    try:
        conn = db.get_connection()
        query = "SELECT COUNT(*) as count FROM tenant_landlord_rights"
        
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()
            count = result['count']
            
            print(f"✓ Total records in table: {count}")
            
            if count == 0:
                print("  ⚠ Warning: No data found in table")
                print("  Run the ingestion script to populate data")
            
            return count
            
    except Exception as e:
        print(f"✗ Error counting records: {e}")
        return None


def test_sample_data():
    """Retrieve and display sample data from the table"""
    print("\n" + "=" * 80)
    print("TEST 4: Sample Data Retrieval")
    print("=" * 80)
    
    try:
        conn = db.get_connection()
        query = """
        SELECT 
            id,
            LEFT(content, 100) as content_preview,
            metadata->>'section_number' as section_number,
            metadata->>'page_number' as page_number,
            metadata->>'source' as source,
            created_at
        FROM tenant_landlord_rights
        ORDER BY id
        LIMIT 5
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                print("✗ No data found in table")
                return False
            
            print(f"✓ Retrieved {len(results)} sample records:\n")
            
            for i, row in enumerate(results, 1):
                print(f"[Record {i}]")
                print(f"  ID: {row['id']}")
                print(f"  Section: {row['section_number']}")
                print(f"  Page: {row['page_number']}")
                print(f"  Source: {row['source']}")
                print(f"  Content Preview: {row['content_preview']}...")
                print(f"  Created At: {row['created_at']}")
                print("-" * 80)
            
            return True
            
    except Exception as e:
        print(f"✗ Error retrieving sample data: {e}")
        return False


def test_embedding_dimensions():
    """Test if embeddings have correct dimensions"""
    print("\n" + "=" * 80)
    print("TEST 5: Embedding Dimensions")
    print("=" * 80)
    
    try:
        conn = db.get_connection()
        query = """
        SELECT 
            id,
            array_length(embedding::real[], 1) as dimension
        FROM tenant_landlord_rights
        LIMIT 5
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                print("✗ No data found to check embeddings")
                return False
            
            print(f"✓ Checking embedding dimensions for {len(results)} records:\n")
            
            all_correct = True
            for row in results:
                dimension = row['dimension']
                status = "✓" if dimension == 3072 else "✗"
                print(f"  {status} Record ID {row['id']}: {dimension} dimensions")
                
                if dimension != 3072:
                    all_correct = False
            
            if all_correct:
                print("\n✓ All embeddings have correct dimensions (3072)")
            else:
                print("\n✗ Some embeddings have incorrect dimensions")
            
            return all_correct
            
    except Exception as e:
        print(f"✗ Error checking embedding dimensions: {e}")
        return False


def test_metadata_structure():
    """Test if metadata has correct structure"""
    print("\n" + "=" * 80)
    print("TEST 6: Metadata Structure")
    print("=" * 80)
    
    try:
        conn = db.get_connection()
        query = """
        SELECT 
            id,
            metadata
        FROM tenant_landlord_rights
        LIMIT 3
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            
            if not results:
                print("✗ No data found to check metadata")
                return False
            
            print(f"✓ Checking metadata structure for {len(results)} records:\n")
            
            required_keys = ['section_number', 'page_number', 'source']
            all_correct = True
            
            for row in results:
                metadata = row['metadata']
                missing_keys = [key for key in required_keys if key not in metadata]
                
                if missing_keys:
                    print(f"  ✗ Record ID {row['id']}: Missing keys {missing_keys}")
                    all_correct = False
                else:
                    print(f"  ✓ Record ID {row['id']}: All required keys present")
                    print(f"     Section: {metadata.get('section_number')}, Page: {metadata.get('page_number')}, Source: {metadata.get('source')}")
            
            if all_correct:
                print("\n✓ All metadata structures are correct")
            else:
                print("\n✗ Some metadata structures are incorrect")
            
            return all_correct
            
    except Exception as e:
        print(f"✗ Error checking metadata structure: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("INGESTION VERIFICATION TEST SUITE")
    print("=" * 80)
    
    results = {
        "Database Connection": False,
        "Table Exists": False,
        "Data Count": None,
        "Sample Data": False,
        "Embedding Dimensions": False,
        "Metadata Structure": False
    }
    
    # Test 1: Database Connection
    results["Database Connection"] = test_database_connection()
    
    if not results["Database Connection"]:
        print("\n✗ Cannot proceed without database connection")
        db.disconnect()
        return
    
    # Test 2: Table Exists
    results["Table Exists"] = test_table_exists()
    
    if not results["Table Exists"]:
        print("\n✗ Cannot proceed without table")
        db.disconnect()
        return
    
    # Test 3: Data Count
    results["Data Count"] = test_data_count()
    
    if results["Data Count"] == 0:
        print("\n⚠ No data in table. Run ingestion script first.")
        db.disconnect()
        return
    
    # Test 4: Sample Data
    results["Sample Data"] = test_sample_data()
    
    # Test 5: Embedding Dimensions
    results["Embedding Dimensions"] = test_embedding_dimensions()
    
    # Test 6: Metadata Structure
    results["Metadata Structure"] = test_metadata_structure()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Database Connection: {'✓ PASS' if results['Database Connection'] else '✗ FAIL'}")
    print(f"Table Exists: {'✓ PASS' if results['Table Exists'] else '✗ FAIL'}")
    print(f"Data Count: {results['Data Count']} records")
    print(f"Sample Data: {'✓ PASS' if results['Sample Data'] else '✗ FAIL'}")
    print(f"Embedding Dimensions: {'✓ PASS' if results['Embedding Dimensions'] else '✗ FAIL'}")
    print(f"Metadata Structure: {'✓ PASS' if results['Metadata Structure'] else '✗ FAIL'}")
    print("=" * 80)
    
    # Disconnect
    db.disconnect()


if __name__ == "__main__":
    run_all_tests()
