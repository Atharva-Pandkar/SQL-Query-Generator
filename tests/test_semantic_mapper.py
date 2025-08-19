import pytest
from unittest.mock import Mock
from semantic_mapper import SemanticMapper
from database import DatabaseManager

class TestSemanticMapper:
    """Unit tests for SemanticMapper class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_db_manager.get_schema_info.return_value = {
            'trips': {
                'columns': [
                    {'name': 'trip_id', 'type': 'integer'},
                    {'name': 'rider_gender', 'type': 'varchar'},
                    {'name': 'started_at', 'type': 'timestamp'},
                    {'name': 'trip_distance_km', 'type': 'numeric'}
                ]
            },
            'stations': {
                'columns': [
                    {'name': 'station_id', 'type': 'integer'},
                    {'name': 'station_name', 'type': 'varchar'}
                ]
            },
            'daily_weather': {
                'columns': [
                    {'name': 'weather_date', 'type': 'date'},
                    {'name': 'precipitation_mm', 'type': 'numeric'}
                ]
            }
        }
        
        self.semantic_mapper = SemanticMapper(self.mock_db_manager)
    
    def test_map_entities_basic(self):
        """Test basic entity mapping"""
        question = "How many women rode bikes?"
        entities = {
            'demographics': [{'type': 'gender', 'value': 'women'}],
            'aggregations': ['count']
        }
        
        mappings = self.semantic_mapper.map_entities_to_schema(question, entities)
        
        # Check that gender filter is properly mapped
        gender_filters = [f for f in mappings['filters'] if 'female' in f['condition']]
        assert len(gender_filters) > 0
        assert gender_filters[0]['condition'] == "rider_gender = 'female'"
        
        # Check that trips table is included
        table_names = [t['name'] for t in mappings['tables']]
        assert 'trips' in table_names
    
    def test_map_weather_conditions(self):
        """Test weather condition mapping"""
        question = "How many rides on rainy days?"
        entities = {
            'weather_conditions': ['rainy'],
            'aggregations': ['count']
        }
        
        mappings = self.semantic_mapper.map_entities_to_schema(question, entities)
        
        # Check weather filter
        weather_filters = [f for f in mappings['filters'] if 'precipitation_mm' in f['condition']]
        assert len(weather_filters) > 0
        assert 'precipitation_mm > 0' in weather_filters[0]['condition']
        
        # Check that daily_weather table is included
        table_names = [t['name'] for t in mappings['tables']]
        assert 'daily_weather' in table_names
    
    def test_map_location_entities(self):
        """Test location entity mapping"""
        question = "Trips from Congress Avenue station"
        entities = {
            'locations': ['congress avenue']
        }
        
        mappings = self.semantic_mapper.map_entities_to_schema(question, entities)
        
        # Check location filter
        location_filters = [f for f in mappings['filters'] if 'Congress Avenue' in f['condition']]
        assert len(location_filters) > 0
        
        # Check stations table is included
        table_names = [t['name'] for t in mappings['tables']]
        assert 'stations' in table_names
    
    def test_similarity_score(self):
        """Test string similarity scoring"""
        # Exact match
        assert self.semantic_mapper._similarity_score("congress", "congress") == 1.0
        
        # Partial match
        score = self.semantic_mapper._similarity_score("congress avenue", "congress")
        assert 0.5 < score < 1.0
        
        # No match
        score = self.semantic_mapper._similarity_score("congress", "xyz")
        assert score < 0.5
    
    def test_score_column_relevance(self):
        """Test column relevance scoring"""
        # Direct word match
        score = self.semantic_mapper.score_column_relevance("trip_distance", "distance traveled")
        assert score > 0.5
        
        # No match
        score = self.semantic_mapper.score_column_relevance("station_id", "weather conditions")
        assert score < 0.3
    
    def test_determine_joins(self):
        """Test join determination logic"""
        mappings = {
            'tables': [
                {'name': 'trips', 'confidence': 0.9},
                {'name': 'stations', 'confidence': 0.8}
            ],
            'joins': []
        }
        
        self.semantic_mapper._determine_joins(mappings, self.mock_db_manager.get_schema_info.return_value)
        
        # Should have added join conditions
        assert len(mappings['joins']) > 0
        
        # Check for typical trip-station joins
        join_conditions = [j['condition'] for j in mappings['joins']]
        assert any('start_station_id' in condition for condition in join_conditions)
    
    def test_find_station_match(self):
        """Test station name matching"""
        # Exact match
        result = self.semantic_mapper._find_station_match("congress avenue")
        assert result == "station_name = 'Congress Avenue'"
        
        # Partial match
        result = self.semantic_mapper._find_station_match("congress")
        assert result == "station_name = 'Congress Avenue'"
        
        # No match
        result = self.semantic_mapper._find_station_match("unknown station")
        assert result is None

if __name__ == '__main__':
    pytest.main([__file__])
