import os
from typing import List, Optional, Dict, Union
from google import genai
from dotenv import load_dotenv
import fitz  # PyMuPDF

# Load environment variables
load_dotenv()

class EmbeddingService:
    """Service for generating embeddings using Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding service with Gemini API
        
        Args:
            api_key: Optional API key. If not provided, will use GEMINI_API_KEY from environment
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure the Gemini API
        self.client = genai.Client(api_key=self.api_key)
        
    def generate_embeddings(self, text: str, model: str = "models/gemini-embedding-001") -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: The text to generate embedding for
            model: The embedding model to use (default: gemini-embedding-001)
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self.client.models.embed_content(
                model=model,
                contents=text,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
            return result.embeddings[0].values
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        model: str = "models/gemini-embedding-001"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to generate embeddings for
            model: The embedding model to use (default: gemini-embedding-001)
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text, model)
            embeddings.append(embedding)
        return embeddings
    
    def generate_query_embedding(self, query: str, model: str = "models/gemini-embedding-001") -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: The search query text
            model: The embedding model to use (default: gemini-embedding-001)
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self.client.models.embed_content(
                model=model,
                contents=query,
                config={"task_type": "RETRIEVAL_QUERY"}
            )
            return result.embeddings[0].values
        except Exception as e:
            raise Exception(f"Error generating query embedding: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def extract_text_from_pdf_by_pages(self, pdf_path: str) -> List[Dict[str, Union[int, str]]]:
        """
        Extract text from a PDF file page by page
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page number and text
        """
        try:
            doc = fitz.open(pdf_path)
            pages = []
            for page_num, page in enumerate(doc, start=1):
                pages.append({
                    "page_number": page_num,
                    "text": page.get_text()
                })
            doc.close()
            return pages
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def generate_pdf_embedding(self, pdf_path: str, model: str = "models/gemini-embedding-001") -> List[float]:
        """
        Generate embedding for an entire PDF file
        
        Args:
            pdf_path: Path to the PDF file
            model: The embedding model to use (default: gemini-embedding-001)
            
        Returns:
            List of floats representing the embedding vector for the entire PDF
        """
        text = self.extract_text_from_pdf(pdf_path)
        return self.generate_embedding(text, model)
    
    def generate_pdf_embeddings_by_pages(
        self, 
        pdf_path: str, 
        model: str = "models/gemini-embedding-001"
    ) -> List[Dict[str, Union[int, str, List[float]]]]:
        """
        Generate embeddings for each page of a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            model: The embedding model to use (default: gemini-embedding-001)
            
        Returns:
            List of dictionaries containing page number, text, and embedding vector
        """
        pages = self.extract_text_from_pdf_by_pages(pdf_path)
        for page in pages:
            page["embedding"] = self.generate_embedding(page["text"], model)
        return pages


# Create a singleton instance
embedding_service = EmbeddingService()
