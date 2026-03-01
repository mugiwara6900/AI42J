import sys
import os

# Add parent directory to path to import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding_service import embedding_service

def test_pdf_embeddings():
    """Test PDF embedding generation"""
    
    # TODO: Replace with your PDF file path
    pdf_path = "C:/Users/23ish/Downloads/Rights of people for AI42J_organized.pdf"
    
    print("=" * 60)
    print("Testing PDF Embedding Service")
    print("=" * 60)
    
    # Test 1: Extract text from PDF
    # print("\n[Test 1] Extracting text from PDF...")
    # try:
    #     text = embedding_service.extract_text_from_pdf(pdf_path)
    #     print(f"✓ Successfully extracted {len(text)} characters")
    #     print(f"First 200 characters: {text[:200]}...")
    # except Exception as e:
    #     print(f"✗ Error: {e}")
    #     return
    
    # Test 2: Extract text by pages
    print("\n[Test 2] Extracting text by pages...")
    try:
        pages = embedding_service.extract_text_from_pdf_by_pages(pdf_path)
        print(f"✓ Successfully extracted {len(pages)} pages")
        for i, page in enumerate(pages):
            print(f"  Page {page['page_number']}: {len(page['text'])} characters")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # # Test 3: Generate embedding for entire PDF
    # print("\n[Test 3] Generating embedding for entire PDF...")
    # try:
    #     embedding = embedding_service.generate_pdf_embedding(pdf_path)
    #     print(f"✓ Successfully generated embedding")
    #     print(f"  Embedding dimension: {len(embedding)}")
    #     print(f"  First 5 values: {embedding[:5]}")
    # except Exception as e:
    #     print(f"✗ Error: {e}")
    #     return
    
    # Test 4: Generate embeddings by pages
    print("\n[Test 4] Generating embeddings for each page...")
    try:
        page_embeddings = embedding_service.generate_pdf_embeddings_by_pages(pdf_path)
        print(f"✓ Successfully generated embeddings for {len(page_embeddings)} pages")
        for i, page in enumerate(page_embeddings):
            print(f"  Page {page['page_number']}: embedding dimension = {len(page['embedding'])}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_pdf_embeddings()
