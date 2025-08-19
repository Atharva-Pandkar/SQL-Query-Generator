import json
import logging
import os
import unicodedata
from typing import Dict, List, Any, Optional
from openai import OpenAI
from .database import DatabaseManager
from .semantic_mapper import SemanticMapper

class QueryGenerator:
    """Generates SQL queries from natural language using LLM"""
    
    def __init__(self, db_manager: DatabaseManager, semantic_mapper: SemanticMapper):
        self.db_manager = db_manager
        self.semantic_mapper = semantic_mapper
        self.openai_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", "default_key")
        )
    
    def generate_query(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question and extracted entities
        Returns: {"sql": str, "params": list, "error": str or None}
        """
        try:
            # Get schema information
            schema_info = self.db_manager.get_schema_info()
            
            # Get semantic mappings for the question
            semantic_mappings = self.semantic_mapper.map_entities_to_schema(question, entities)
            
            # Generate SQL using LLM
            sql_result = self._generate_sql_with_llm(question, entities, schema_info, semantic_mappings)
            
            return sql_result
            
        except Exception as e:
            logging.error(f"Query generation failed: {e}")
            return {
                "sql": None,
                "params": [],
                "error": f"Query generation error: {str(e)}"
            }
    
    def _generate_sql_with_llm(self, question: str, entities: Dict[str, Any], 
                               schema_info: Dict[str, Any], 
                               semantic_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI GPT-4o to generate SQL query"""
        
        # Prepare schema information for the LLM
        schema_description = self._format_schema_for_llm(schema_info)
        
        # Create system prompt - using string concatenation to avoid f-string issues with JSON
        system_prompt = """You are an expert SQL query generator for a bike-share analytics system.

DATABASE SCHEMA:
""" + schema_description + """

SEMANTIC MAPPINGS:
""" + json.dumps(semantic_mappings, indent=2) + """

RULES:
1. Generate ONLY parameterized SQL queries (use %s for parameters)
2. NEVER use string concatenation or f-strings
3. Always use proper JOINs when multiple tables are needed
4. For date/time filters, use appropriate PostgreSQL date functions
5. Handle aggregations (COUNT, AVG, SUM, MAX, MIN) based on the question
6. Use CASE statements for conditional logic
7. Always validate that column names exist in the schema
8. ONLY generate SELECT queries - NEVER DELETE, UPDATE, INSERT, or DROP
9. If question is not bike-share related, set sql to null and include error message
10. Only use tables: bikes, trips, stations, daily_weather
11. IMPORTANT: The trips table has columns: trip_id, started_at, ended_at, start_station_id, end_station_id, bike_id, trip_distance_km, rider_birth_year, rider_gender
12. For weekend queries, use EXTRACT(DOW FROM started_at) IN (0, 6) where 0=Sunday, 6=Saturday  
13. Always use "started_at" and "ended_at" for trip timestamps - NEVER "start_time" or "end_time"

WEATHER CONDITIONS:
- "rainy days" means precipitation_mm > 0

WEEKEND DETECTION:
- Use EXTRACT(DOW FROM started_at) IN (0, 6) for weekends (0=Sunday, 6=Saturday)

COMMON BIKE COUNT PATTERNS:
- "how many bikes were used" = COUNT(DISTINCT trip_id) FROM trips
- "bikes used on weekend" = COUNT(DISTINCT trip_id) FROM trips WHERE EXTRACT(DOW FROM started_at) IN (0, 6)
- "sunny days" means precipitation_mm = 0

TIME PERIODS:
- "last month" for June 2025 means WHERE DATE_PART('month', started_at) = 6 AND DATE_PART('year', started_at) = 2025
- "first week of June 2025" means WHERE started_at BETWEEN '2025-06-01' AND '2025-06-07'

GENDER MAPPING:
- "women" maps to rider_gender = 'female'
- "men" maps to rider_gender = 'male'

COLUMN NAME CORRECTIONS:
- Use "started_at" not "start_time"
- Use "ended_at" not "end_time"
- Use "rider_gender" not "gender"
- Use "rider_birth_year" not "birth_year"

BIKE MODELS - CRITICAL UNICODE HANDLING:
- Use EXACT bike model names: 'E‑Bike', 'Classic', 'Step‑Thru'
- E‑Bike and Step‑Thru use Unicode U+2011 (‑) NOT ASCII hyphen (-)
- When generating bike_model filters, use these exact Unicode strings
- Example: bike_model = 'E‑Bike' (with Unicode ‑ hyphen)

Return JSON in this exact format:
{
    "sql": "SELECT ... FROM ... WHERE ... ",
    "params": [param1, param2, ...],
    "explanation": "Brief explanation of the query logic"
}"""

        user_prompt = f"""
Convert this natural language question to SQL:
"{question}"

Extracted entities: {json.dumps(entities, indent=2)}

Focus on:
1. Identifying the main metric requested (count, average, sum, etc.)
2. Applying appropriate filters based on entities
3. Joining tables as needed
4. Using parameterized queries for safety
"""

        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content is None:
                return {
                    "sql": None,
                    "params": [],
                    "error": "LLM returned empty response"
                }
            result = json.loads(content)
            
            # Check if LLM returned an error for irrelevant questions
            if result.get('error'):
                return {
                    "sql": None,
                    "params": [],
                    "error": result['error']
                }
            
            # Validate the response
            if not result.get('sql'):
                return {
                    "sql": None,
                    "params": [],
                    "error": "LLM failed to generate SQL query"
                }
            
            # Validate SQL query safety
            sql_validation = self._validate_sql_safety(result['sql'])
            if not sql_validation['safe']:
                logging.error(f"SQL validation failed: {sql_validation['error']}")
                logging.error(f"Generated SQL: {result['sql']}")
                return {
                    "sql": None,
                    "params": [],
                    "error": "Sorry, I couldn't process your question. Please try asking about bike trips, station usage, or weather data."
                }
            
            # Normalize bike model parameters to handle Unicode characters
            normalized_params = self._normalize_bike_model_params(result.get('params', []))
            
            return {
                "sql": result['sql'],
                "params": normalized_params,
                "error": None
            }
            
        except Exception as e:
            logging.error(f"LLM query generation failed: {e}")
            return {
                "sql": None,
                "params": [],
                "error": "Sorry, I couldn't understand your question. Please try asking about bike trips, stations, or weather data."
            }
    
    def _normalize_bike_model_params(self, params: List[Any]) -> List[Any]:
        """Normalize bike model parameters to handle Unicode characters properly"""
        normalized_params = []
        
        # Define the correct Unicode bike model mappings
        bike_model_map = {
            'E-Bike': 'E‑Bike',      # ASCII hyphen → Unicode U+2011
            'e-bike': 'E‑Bike',
            'electric': 'E‑Bike',
            'Step-Thru': 'Step‑Thru',  # ASCII hyphen → Unicode U+2011
            'step-thru': 'Step‑Thru',
            'Classic': 'Classic'        # No change needed
        }
        
        for param in params:
            if isinstance(param, str):
                # Check if this parameter is a bike model that needs normalization
                normalized_param = bike_model_map.get(param, param)
                # Also handle case variations
                for ascii_name, unicode_name in bike_model_map.items():
                    if param.lower() == ascii_name.lower():
                        normalized_param = unicode_name
                        break
                normalized_params.append(normalized_param)
            else:
                normalized_params.append(param)
        
        return normalized_params
    
    def _validate_sql_safety(self, sql: str) -> Dict[str, Any]:
        """Validate that the SQL query is safe and appropriate"""
        sql_upper = sql.upper().strip()
        
        # Check for dangerous operations
        dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 'TRUNCATE', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return {
                    "safe": False,
                    "error": f"Query contains unsafe operation: {keyword}. Only SELECT queries are allowed."
                }
        
        # Simple table validation - only check main FROM clause (not functions)
        allowed_tables = ['bikes', 'trips', 'stations', 'daily_weather']
        
        # Much simpler approach: split by keywords and check what follows FROM
        sql_words = sql_upper.split()
        
        # Find main table references after FROM (avoiding function contexts)
        for i, word in enumerate(sql_words):
            if word == 'FROM' and i + 1 < len(sql_words):
                # Check if this FROM is not inside a function call
                # Look back to see if we're inside parentheses
                context_before = ' '.join(sql_words[max(0, i-3):i])
                
                # Skip if this FROM appears to be inside a function (has parentheses before it)
                if '(' in context_before and ')' not in context_before:
                    continue
                    
                next_word = sql_words[i + 1].lower().strip('(),;')
                if next_word not in allowed_tables and not next_word.startswith('('):
                    return {
                        "safe": False,
                        "error": f"Query references unknown table '{next_word}'. Available tables: {', '.join(allowed_tables)}"
                    }
        
        return {"safe": True, "error": None}
    
    def _format_schema_for_llm(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for LLM consumption"""
        schema_text = ""
        
        for table_name, table_info in schema_info.items():
            schema_text += f"\nTable: {table_name}\n"
            schema_text += "Columns:\n"
            
            for column in table_info['columns']:
                schema_text += f"  - {column['name']} ({column['type']})"
                if not column['nullable']:
                    schema_text += " NOT NULL"
                if column['key_type'] == 'PRIMARY KEY':
                    schema_text += " PRIMARY KEY"
                schema_text += "\n"
            
            if table_info['foreign_keys']:
                schema_text += "Foreign Keys:\n"
                for fk in table_info['foreign_keys']:
                    schema_text += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
        
        return schema_text
    
    def validate_sql_safety(self, sql: str) -> bool:
        """
        Validate that SQL query is safe and uses parameterized queries
        Returns True if safe, False otherwise
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            r"';",  # SQL injection attempt
            r"--",  # SQL comments
            r"/\*",  # Multi-line comments
            r"UNION",  # Union attacks
            r"DROP",  # DDL statements
            r"DELETE",  # DML without WHERE (should be caught by business logic)
            r"UPDATE",  # DML without WHERE
            r"INSERT",  # DML statements
            r"CREATE",  # DDL statements
            r"ALTER",   # DDL statements
        ]
        
        sql_upper = sql.upper()
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                logging.warning(f"Potentially unsafe SQL pattern detected: {pattern}")
                return False
        
        # Ensure query uses parameterized format (%s)
        if "'" in sql and "%s" not in sql:
            logging.warning("SQL contains string literals without parameterization")
            return False
        
        return True
