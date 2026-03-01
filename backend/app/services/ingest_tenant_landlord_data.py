import sys
import os
import re
import json
from typing import List, Dict, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db
from app.services.embedding_service import embedding_service

class LegalDocumentIngestor:
    """Process legal PDF and store as vector embeddings in PostgreSQL"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the ingestor
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = r"C:\Users\23ish\Downloads\Rights of people for AI42J_organized.pdf"
        self.table_name = "tenant_landlord_rights"
        self.source_name = "Model Tenancy Act 2021"
        self.start_page = 1  # Pages 4 to 25
        self.end_page = 25
        
    def extract_and_chunk_pages(self) -> List[Dict]:
        """
        Extract pages 4-25 and chunk by sections using embedding service
        
        Returns:
            List of chunks with content, section_number, page_number, and embedding
        """
        print(f"\n[1/3] Extracting and chunking pages {self.start_page} to {self.end_page}...")
        
        try:
            # Use embedding service to extract all pages
            all_pages = embedding_service.extract_text_from_pdf_by_pages(self.pdf_path)
            
            # Filter to only pages 4-25
            filtered_pages = [
                page for page in all_pages 
                if self.start_page <= page['page_number'] <= self.end_page
            ]
            
            print(f"✓ Extracted {len(filtered_pages)} pages")
            
            # Chunk by sections
            chunks = []
            section_pattern = re.compile(r'(\d+)\.\s+([A-Z][^\n]+)')
            
            for page in filtered_pages:
                page_num = page['page_number']
                text = page['text']
                
                # Find all section headers in the page
                matches = list(section_pattern.finditer(text))
                
                if not matches:
                    # No sections found, treat entire page as one chunk
                    if text.strip():
                        chunks.append({
                            "content": text.strip(),
                            "section_number": None,
                            "page_number": page_num
                        })
                    continue
                
                # Process each section
                for i, match in enumerate(matches):
                    section_num = match.group(1)
                    section_start = match.start()
                    
                    # Determine section end (start of next section or end of text)
                    if i + 1 < len(matches):
                        section_end = matches[i + 1].start()
                    else:
                        section_end = len(text)
                    
                    # Extract section content
                    section_content = text[section_start:section_end].strip()
                    
                    if section_content:
                        chunks.append({
                            "content": section_content,
                            "section_number": int(section_num),
                            "page_number": page_num
                        })
            
            print(f"✓ Created {len(chunks)} chunks from sections")
            return chunks
            
        except Exception as e:
            raise Exception(f"Error extracting and chunking pages: {str(e)}")
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for each chunk using embedding service
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with embeddings added
        """
        print(f"\n[2/3] Generating embeddings for {len(chunks)} chunks...")
        successful = 0
        failed = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Use embedding service to generate embedding
                embedding = embedding_service.generate_embedding(chunk['content'])
                chunk['embedding'] = embedding
                successful += 1
                
                if (i + 1) % 5 == 0:
                    print(f"  Progress: {i + 1}/{len(chunks)} chunks processed")
                    
            except Exception as e:
                print(f"✗ Error generating embedding for chunk {i + 1}: {str(e)}")
                chunk['embedding'] = None
                failed += 1
        
        print(f"✓ Generated {successful} embeddings successfully")
        if failed > 0:
            print(f"✗ Failed to generate {failed} embeddings")
        
        # Filter out chunks without embeddings
        chunks_with_embeddings = [c for c in chunks if c['embedding'] is not None]
        return chunks_with_embeddings
    
    def insert_into_database(self, chunks: List[Dict]) -> Tuple[int, int]:
        """
        Insert chunks into PostgreSQL database
        
        Args:
            chunks: List of chunks with embeddings
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        print(f"\n[3/3] Inserting {len(chunks)} chunks into database...")
        
        conn = db.get_connection()
        successful = 0
        failed = 0
        
        # Insert each chunk individually for better error handling
        for i, chunk in enumerate(chunks):
            try:
                with conn.cursor() as cur:
                    # Prepare metadata
                    metadata = {
                        "section_number": chunk['section_number'],
                        "page_number": chunk['page_number'],
                        "source": self.source_name
                    }
                    
                    # Insert query with halfvec casting
                    query = f"""
                    INSERT INTO {self.table_name} (content, embedding, metadata)
                    VALUES (%s, %s::halfvec, %s)
                    """
                    
                    cur.execute(query, (
                        chunk['content'],
                        chunk['embedding'],
                        json.dumps(metadata)
                    ))
                    conn.commit()
                    successful += 1
                    
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i + 1}/{len(chunks)} chunks inserted")
                        
            except Exception as e:
                print(f"✗ Error inserting chunk {i + 1} (Section {chunk.get('section_number', 'N/A')}, Page {chunk['page_number']}): {str(e)}")
                conn.rollback()
                failed += 1
                continue
        
        print(f"✓ Successfully inserted {successful} chunks")
        if failed > 0:
            print(f"✗ Failed to insert {failed} chunks")
        
        return successful, failed
    
    def process(self):
        """Main processing pipeline"""
        print("=" * 70)
        print("Legal Document Ingestion Pipeline")
        print("=" * 70)
        print(f"PDF: {self.pdf_path}")
        print(f"Target Table: {self.table_name}")
        print(f"Pages: {self.start_page} to {self.end_page}")
        print(f"Using: embedding_service for PDF extraction and embeddings")
        
        try:
            # Step 1: Extract pages and chunk by sections
            chunks = self.extract_and_chunk_pages()
            
            # Step 2: Generate embeddings using embedding service
            chunks_with_embeddings = self.generate_embeddings(chunks)
            
            # Step 3: Insert into database
            db.connect()
            successful, failed = self.insert_into_database(chunks_with_embeddings)
            
            # Summary
            print("\n" + "=" * 70)
            print("Processing Complete!")
            print("=" * 70)
            print(f"Total chunks processed: {len(chunks)}")
            print(f"Successfully inserted: {successful}")
            print(f"Failed: {failed}")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n✗ Fatal error: {str(e)}")
            raise
        finally:
            db.disconnect()


def main():
    """Main entry point"""
    # TODO: Replace with your PDF file path
    pdf_path = "path/to/your/legal_document.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        print("Please update the pdf_path variable with the correct path.")
        return
    
    ingestor = LegalDocumentIngestor(pdf_path)
    ingestor.process()


if __name__ == "__main__":
    main()
