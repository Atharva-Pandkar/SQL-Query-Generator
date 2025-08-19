import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class DatabaseManager:
    """Handles PostgreSQL database connections and queries"""
    load_dotenv()
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': 5432,
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        self._schema_cache = None
    
    def get_connection(self):
        """Create and return a database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            raise
    
    def test_connection(self):
        """Test database connectivity"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
    
    def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a parameterized SQL query and return results
        Uses parameterized queries to prevent SQL injection
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    
                    if cur.description:
                        results = cur.fetchall()
                        return [dict(row) for row in results]
                    else:
                        return []
                        
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            raise
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Dynamically introspect database schema using information_schema
        Returns detailed information about tables and columns
        """
        if self._schema_cache:
            return self._schema_cache
        
        schema_query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            CASE 
                WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                ELSE 'REGULAR'
            END as key_type,
            fk.foreign_table_name,
            fk.foreign_column_name
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
        LEFT JOIN (
            SELECT 
                kcu.column_name, 
                kcu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
        LEFT JOIN (
            SELECT 
                kcu.column_name,
                kcu.table_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        ) fk ON c.column_name = fk.column_name AND c.table_name = fk.table_name
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        try:
            results = self.execute_query(schema_query)
            
            # Organize schema information by table
            schema_info = {}
            for row in results:
                table_name = row['table_name']
                if table_name not in schema_info:
                    schema_info[table_name] = {
                        'columns': [],
                        'primary_keys': [],
                        'foreign_keys': []
                    }
                
                if row['column_name']:  # Skip tables without columns
                    column_info = {
                        'name': row['column_name'],
                        'type': row['data_type'],
                        'nullable': row['is_nullable'] == 'YES',
                        'default': row['column_default'],
                        'max_length': row['character_maximum_length'],
                        'precision': row['numeric_precision'],
                        'scale': row['numeric_scale'],
                        'key_type': row['key_type']
                    }
                    
                    schema_info[table_name]['columns'].append(column_info)
                    
                    if row['key_type'] == 'PRIMARY KEY':
                        schema_info[table_name]['primary_keys'].append(row['column_name'])
                    elif row['key_type'] == 'FOREIGN KEY':
                        schema_info[table_name]['foreign_keys'].append({
                            'column': row['column_name'],
                            'references_table': row['foreign_table_name'],
                            'references_column': row['foreign_column_name']
                        })
            
            self._schema_cache = schema_info
            return schema_info
            
        except Exception as e:
            logging.error(f"Schema introspection failed: {e}")
            raise
    
    def get_sample_values(self, table_name: str, column_name: str, limit: int = 10) -> List[Any]:
        """Get sample values from a column for semantic mapping"""
        try:
            query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT %s"
            results = self.execute_query(query, [limit])
            return [list(row.values())[0] for row in results]
        except Exception as e:
            logging.error(f"Failed to get sample values for {table_name}.{column_name}: {e}")
            return []
