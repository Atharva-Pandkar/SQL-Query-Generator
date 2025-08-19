import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from query_generator import QueryGenerator
from database import DatabaseManager
from semantic_mapper import SemanticMapper

class TestQueryGenerator:
    """Unit tests for QueryGenerator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_semantic_mapper = Mock(spec=SemanticMapper)
        
        # Mock schema info
        self.mock_db_manager.get_schema_info.return_value = {
            'trips': {
                'columns': [
                    {'name': 'trip_id', 'type': 'integer', 'nullable': False, 'key_type': 'PRIMARY KEY'},
                    {'name': 'started_at', 'type': 'timestamp', 'nullable': True, 'key_type': 'REGULAR'},
                    {'name': 'rider_gender', 'type': 'varchar', 'nullable': True, 'key_type': 'REGULAR'},
                    {'name': 'trip_distance_km', 'type': 'numeric', 'nullable': True, 'key_type': 'REGULAR'}
                ],
                'primary_keys': ['trip_id'],
                'foreign_keys': []
            },
            'stations': {
                'columns': [
                    {'name': 'station_id', 'type': 'integer', 'nullable': False, 'key_type': 'PRIMARY KEY'},
                    {'name': 'station_name', 'type': 'varchar', 'nullable': False, 'key_type': 'REGULAR'}
                ],
                'primary_keys': ['station_id'],
                'foreign_keys': []
            }
        }
        
        self.query_generator = QueryGenerator(self.mock_db_manager, self.mock_semantic_mapper)
    
    @patch('query_generator.OpenAI')
    def test_generate_query_success(self, mock_openai):
        """Test successful query generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "sql": "SELECT AVG(EXTRACT(EPOCH FROM (ended_at - started_at))/60) FROM trips t JOIN stations s ON t.start_station_id = s.station_id WHERE s.station_name = %s AND DATE_PART('month', started_at) = %s AND DATE_PART('year', started_at) = %s",
            "params": ["Congress Avenue", 6, 2025],
            "explanation": "Calculate average ride time in minutes for trips starting from Congress Avenue in June 2025"
        }
        '''
        
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        # Mock semantic mapping
        self.mock_semantic_mapper.map_entities_to_schema.return_value = {
            'tables': [{'name': 'trips', 'confidence': 0.9}],
            'filters': [{'condition': "station_name = 'Congress Avenue'", 'confidence': 0.95}],
            'date_filters': [{'condition': "DATE_PART('month', started_at) = 6", 'confidence': 0.9}]
        }
        
        question = "What was the average ride time for journeys that started at Congress Avenue in June 2025?"
        entities = {
            'locations': ['congress avenue'],
            'time_periods': ['june 2025'],
            'aggregations': ['average']
        }
        
        result = self.query_generator.generate_query(question, entities)
        
        assert result['error'] is None
        assert 'SELECT AVG' in result['sql']
        assert result['params'] == ["Congress Avenue", 6, 2025]
    
    @patch('query_generator.OpenAI')
    def test_generate_query_llm_error(self, mock_openai):
        """Test handling of LLM errors"""
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        self.mock_semantic_mapper.map_entities_to_schema.return_value = {}
        
        result = self.query_generator.generate_query("test question", {})
        
        assert result['error'] is not None
        assert "LLM generation error" in result['error']
        assert result['sql'] is None
    
    def test_validate_sql_safety_secure(self):
        """Test SQL safety validation for secure queries"""
        safe_sql = "SELECT COUNT(*) FROM trips WHERE rider_gender = %s AND started_at > %s"
        
        assert self.query_generator.validate_sql_safety(safe_sql) is True
    
    def test_validate_sql_safety_dangerous(self):
        """Test SQL safety validation for dangerous queries"""
        dangerous_queries = [
            "SELECT * FROM trips; DROP TABLE trips;",
            "SELECT * FROM trips WHERE name = 'test' OR 1=1",
            "SELECT * FROM trips /* comment */ WHERE id = 1",
            "SELECT * FROM trips UNION SELECT * FROM users"
        ]
        
        for query in dangerous_queries:
            assert self.query_generator.validate_sql_safety(query) is False
    
    def test_format_schema_for_llm(self):
        """Test schema formatting for LLM consumption"""
        schema_text = self.query_generator._format_schema_for_llm(
            self.mock_db_manager.get_schema_info.return_value
        )
        
        assert "Table: trips" in schema_text
        assert "Table: stations" in schema_text
        assert "trip_id (integer) NOT NULL PRIMARY KEY" in schema_text
        assert "station_name (varchar) NOT NULL" in schema_text

if __name__ == '__main__':
    pytest.main([__file__])
