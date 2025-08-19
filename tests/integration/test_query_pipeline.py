import pytest
from app import app
from database import DatabaseManager
from nlp_service import NLPService
from query_generator import QueryGenerator
from semantic_mapper import SemanticMapper

class TestQueryPipeline:
    """Integration tests for the complete query pipeline"""

    @pytest.fixture
    def setup_services(self, db_manager):
        """Set up all required services"""
        nlp_service = NLPService()
        semantic_mapper = SemanticMapper(db_manager)
        query_generator = QueryGenerator(db_manager, semantic_mapper)
        return nlp_service, semantic_mapper, query_generator

    def test_full_query_pipeline(self, setup_services, client):
        """Test the complete query pipeline from natural language to results"""
        nlp_service, semantic_mapper, query_generator = setup_services
        
        # Test case 1: Average ride time query
        question = "What was the average ride time for journeys that started at Congress Avenue in June 2025?"
        
        # Step 1: Extract entities
        entities = nlp_service.extract_entities(question)
        assert entities is not None
        assert 'locations' in entities
        assert 'dates' in entities
        
        # Step 2: Generate SQL
        result = query_generator.generate_query(question, entities)
        assert result is not None
        assert 'sql' in result
        assert 'params' in result
        assert result.get('error') is None
        
        # Step 3: Test API endpoint
        response = client.post('/query',
                             json={'question': question},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('error') is None
        assert data.get('sql') is not None
        assert data.get('result') is not None

    def test_weather_related_query(self, setup_services, client):
        """Test pipeline with weather-related query"""
        question = "How many trips were made on rainy days in June 2025?"
        
        response = client.post('/query',
                             json={'question': question},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert 'precipitation_mm' in data.get('sql', '')

    def test_demographic_query(self, setup_services, client):
        """Test pipeline with demographic query"""
        question = "What's the average trip distance for women riders?"
        
        response = client.post('/query',
                             json={'question': question},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert 'rider_gender' in data.get('sql', '')

    def test_complex_query(self, setup_services, client):
        """Test pipeline with complex query combining multiple aspects"""
        question = "What was the average trip distance for women starting from Congress Avenue on rainy weekends in June 2025?"
        
        response = client.post('/query',
                             json={'question': question},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        sql = data.get('sql', '')
        assert 'rider_gender' in sql
        assert 'station_name' in sql
        assert 'precipitation_mm' in sql
        assert 'EXTRACT(ISODOW FROM' in sql  # Weekend check
