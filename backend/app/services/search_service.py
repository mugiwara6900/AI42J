import sys
import os
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db
from app.services.embedding_service import embedding_service


class SearchService:
    """Service for searching legal documents using vector similarity"""
    
    def __init__(self):
        """Initialize the search service"""
        self.table_name = "tenant_landlord_rights"
    
    def search_legal_docs(self, query_text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Search legal documents using vector similarity
        
        Args:
            query_text: The search query text
            limit: Number of results to return (default: 3)
            
        Returns:
            List of dictionaries containing:
                - content: The document text
                - section_number: Section number from metadata
                - page_number: Page number from metadata
                - distance: Cosine distance score (lower is better)
        """
        try:
            # Generate embeddings for the query
            query_embeddings = embedding_service.generate_embeddings(query_text)
            
            # Get database connection
            conn = db.get_connection()
            
            # Query with cosine similarity using <=> operator
            query = f"""
            SELECT 
                content,
                metadata->>'section_number' as section_number,
                metadata->>'page_number' as page_number,
                metadata->>'source' as source,
                embeddings <=> %s::halfvec as distance
            FROM {self.table_name}
            ORDER BY distance
            LIMIT %s
            """
            
            with conn.cursor() as cur:
                cur.execute(query, (query_embeddings, limit))
                results = cur.fetchall()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "content": row['content'],
                    "section_number": row['section_number'],
                    "page_number": row['page_number'],
                    "source": row['source'],
                    "distance": float(row['distance'])
                })
            
            return formatted_results
            
        except Exception as e:
            raise Exception(f"Error searching legal documents: {str(e)}")
    
    def search_with_metadata_filter(
        self, 
        query_text: str, 
        section_number: int = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search legal documents with optional metadata filtering
        
        Args:
            query_text: The search query text
            section_number: Optional section number to filter by
            limit: Number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Generate embeddings for the query
            query_embeddings = embedding_service.generate_embeddings(query_text)
            
            # Get database connection
            conn = db.get_connection()
            
            # Build query with optional filtering
            if section_number is not None:
                query = f"""
                SELECT 
                    content,
                    metadata->>'section_number' as section_number,
                    metadata->>'page_number' as page_number,
                    metadata->>'source' as source,
                    embeddings <=> %s::halfvec as distance
                FROM {self.table_name}
                WHERE (metadata->>'section_number')::int = %s
                ORDER BY distance
                LIMIT %s
                """
                params = (query_embeddings, section_number, limit)
            else:
                query = f"""
                SELECT 
                    content,
                    metadata->>'section_number' as section_number,
                    metadata->>'page_number' as page_number,
                    metadata->>'source' as source,
                    embeddings <=> %s::halfvec as distance
                FROM {self.table_name}
                ORDER BY distance
                LIMIT %s
                """
                params = (query_embeddings, limit)
            
            with conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
            
            # Format results
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "content": row['content'],
                    "section_number": row['section_number'],
                    "page_number": row['page_number'],
                    "source": row['source'],
                    "distance": float(row['distance'])
                })
            
            return formatted_results
            
        except Exception as e:
            raise Exception(f"Error searching with metadata filter: {str(e)}")


# Create a singleton instance
search_service = SearchService()
