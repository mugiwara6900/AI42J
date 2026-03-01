import os
from typing import Optional, List
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    """PostgreSQL database connection manager using psycopg"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            connection_string: Optional database URL. If not provided, will use DATABASE_URL from environment
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("DATABASE_URL not found in environment variables")
        
    def connect(self):
        """Establish connection to the database"""
        try:
            self.conn = psycopg.connect(
                self.connection_string,
                row_factory=dict_row,  # Return results as dictionaries
                autocommit=True
            )
            # Register pgvector extension
            register_vector(self.conn)
            print("✓ Database connection established successfully")
            print("✓ pgvector extension registered")
            return self.conn
        except Exception as e:
            raise Exception(f"Error connecting to database: {str(e)}")
        except Exception as e:
            raise Exception(f"Error connecting to database: {str(e)}")
    
    def disconnect(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✓ Database connection closed")
    
    def get_connection(self) -> psycopg.Connection:
        """
        Get the current connection or create a new one
        
        Returns:
            Active database connection
        """
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn
    
    def execute_query(self, query: str, params: Optional[tuple] = None):
        """
        Execute a query and return results
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            
        Returns:
            Query results as list of dictionaries
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:  # SELECT query
                    return cur.fetchall()
                conn.commit()  # INSERT/UPDATE/DELETE query
                return None
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error executing query: {str(e)}")
    
    def execute_many(self, query: str, params_list: list):
        """
        Execute a query multiple times with different parameters
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                conn.commit()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            raise Exception(f"Error executing batch query: {str(e)}")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def enable_pgvector(self):
        """Enable pgvector extension in the database"""
        try:
            self.execute_query("CREATE EXTENSION IF NOT EXISTS vector")
            print("✓ pgvector extension enabled")
        except Exception as e:
            raise Exception(f"Error enabling pgvector: {str(e)}")
    
    def create_vector_table(self, table_name: str, vector_dimension: int = 768):
        """
        Create a table for storing vectors
        
        Args:
            table_name: Name of the table to create
            vector_dimension: Dimension of the vector (default: 768 for Gemini embeddings)
        """
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embeddings vector({vector_dimension}),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            self.execute_query(query)
            print(f"✓ Table '{table_name}' created successfully")
        except Exception as e:
            raise Exception(f"Error creating vector table: {str(e)}")
    
    def create_vector_index(self, table_name: str, index_type: str = "hnsw"):
        """
        Create an index on the vector column for faster similarity search
        
        Args:
            table_name: Name of the table
            index_type: Type of index ('hnsw' or 'ivfflat')
        """
        index_name = f"{table_name}_embeddings_idx"
        
        if index_type == "hnsw":
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON {table_name} 
            USING hnsw (embeddings vector_cosine_ops)
            """
        elif index_type == "ivfflat":
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_name} 
            ON {table_name} 
            USING ivfflat (embeddings vector_cosine_ops)
            WITH (lists = 100)
            """
        else:
            raise ValueError("index_type must be 'hnsw' or 'ivfflat'")
        
        try:
            self.execute_query(query)
            print(f"✓ {index_type.upper()} index created on '{table_name}'")
        except Exception as e:
            raise Exception(f"Error creating vector index: {str(e)}")
    
    def insert_vector(self, table_name: str, content: str, embeddings: List[float], metadata: dict = None):
        """
        Insert a vector into the table
        
        Args:
            table_name: Name of the table
            content: Text content
            embeddings: Vector embeddings
            metadata: Optional metadata as dictionary
        """
        query = f"""
        INSERT INTO {table_name} (content, embeddings, metadata)
        VALUES (%s, %s, %s)
        RETURNING id
        """
        try:
            result = self.execute_query(query, (content, embeddings, metadata))
            return result[0]['id'] if result else None
        except Exception as e:
            raise Exception(f"Error inserting vector: {str(e)}")
    
    def insert_vectors_batch(self, table_name: str, data: List[dict]):
        """
        Insert multiple vectors in batch
        
        Args:
            table_name: Name of the table
            data: List of dictionaries with 'content', 'embeddings', and optional 'metadata'
        """
        query = f"""
        INSERT INTO {table_name} (content, embeddings, metadata)
        VALUES (%s, %s, %s)
        """
        params_list = [
            (item['content'], item['embeddings'], item.get('metadata'))
            for item in data
        ]
        try:
            self.execute_many(query, params_list)
            print(f"✓ Inserted {len(data)} vectors into '{table_name}'")
        except Exception as e:
            raise Exception(f"Error inserting vectors batch: {str(e)}")
    
    def similarity_search(
        self, 
        table_name: str, 
        query_embeddings: List[float], 
        limit: int = 5,
        distance_metric: str = "cosine"
    ):
        """
        Perform similarity search using vector embeddings
        
        Args:
            table_name: Name of the table
            query_embeddings: Query vector embeddings
            limit: Number of results to return
            distance_metric: Distance metric ('cosine', 'l2', or 'inner_product')
            
        Returns:
            List of similar items with their distances
        """
        # Choose the distance operator based on metric
        if distance_metric == "cosine":
            operator = "<=>"
        elif distance_metric == "l2":
            operator = "<->"
        elif distance_metric == "inner_product":
            operator = "<#>"
        else:
            raise ValueError("distance_metric must be 'cosine', 'l2', or 'inner_product'")
        
        query = f"""
        SELECT id, content, metadata, 
               embeddings {operator} %s AS distance
        FROM {table_name}
        ORDER BY distance
        LIMIT %s
        """
        try:
            results = self.execute_query(query, (query_embeddings, limit))
            return results
        except Exception as e:
            raise Exception(f"Error performing similarity search: {str(e)}")


# Create a singleton instance
db = Database().connect()


# Create a singleton instance
db = Database()
