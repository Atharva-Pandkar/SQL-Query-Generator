import pytest
from nlp_service import NLPService

class TestNLPService:
    """Unit tests for NLPService class"""

    @pytest.fixture
    def nlp_service(self):
        """Create an NLPService instance"""
        return NLPService()

    def test_extract_entities_basic(self, nlp_service):
        """Test basic entity extraction"""
        question = "How many bikes were used on June 1st, 2025?"
        entities = nlp_service.extract_entities(question)
        
        assert 'dates' in entities
        assert any('2025' in date for date in entities['dates'])
        assert 'aggregations' in entities
        assert 'count' in entities['aggregations']

    def test_extract_entities_location(self, nlp_service):
        """Test location entity extraction"""
        question = "Show me trips from Congress Avenue station"
        entities = nlp_service.extract_entities(question)
        
        assert 'locations' in entities
        assert 'congress avenue' in [loc.lower() for loc in entities['locations']]

    def test_extract_entities_weather(self, nlp_service):
        """Test weather condition extraction"""
        question = "How many trips happened on rainy days?"
        entities = nlp_service.extract_entities(question)
        
        assert 'weather_conditions' in entities
        assert 'rainy' in entities['weather_conditions']

    def test_extract_entities_demographics(self, nlp_service):
        """Test demographic entity extraction"""
        question = "What's the average trip distance for women riders?"
        entities = nlp_service.extract_entities(question)
        
        assert 'demographics' in entities
        assert any('women' in demo.lower() for demo in entities['demographics'])
        assert 'aggregations' in entities
        assert 'average' in entities['aggregations']

    def test_extract_entities_time_periods(self, nlp_service):
        """Test time period extraction"""
        question = "Show me morning rides during weekends"
        entities = nlp_service.extract_entities(question)
        
        assert 'time_periods' in entities
        assert any('morning' in period.lower() for period in entities['time_periods'])
        assert any('weekend' in period.lower() for period in entities['time_periods'])

    def test_extract_entities_measurements(self, nlp_service):
        """Test measurement extraction"""
        question = "What's the total distance traveled in kilometers?"
        entities = nlp_service.extract_entities(question)
        
        assert 'measurements' in entities
        assert any('distance' in measure.lower() for measure in entities['measurements'])
        assert 'aggregations' in entities
        assert 'total' in entities['aggregations']

    def test_extract_entities_complex_query(self, nlp_service):
        """Test entity extraction from complex queries"""
        question = "What was the average ride time for women starting from Congress Avenue on rainy weekends in June 2025?"
        entities = nlp_service.extract_entities(question)
        
        assert 'demographics' in entities
        assert 'locations' in entities
        assert 'weather_conditions' in entities
        assert 'time_periods' in entities
        assert 'dates' in entities
        assert 'aggregations' in entities

    def test_extract_entities_empty_query(self, nlp_service):
        """Test handling of empty queries"""
        entities = nlp_service.extract_entities("")
        
        assert all(isinstance(value, list) for value in entities.values())
        assert all(len(value) == 0 for value in entities.values())

    def test_extract_entities_invalid_input(self, nlp_service):
        """Test handling of invalid input"""
        entities = nlp_service.extract_entities(None)
        
        assert all(isinstance(value, list) for value in entities.values())
        assert all(len(value) == 0 for value in entities.values())
