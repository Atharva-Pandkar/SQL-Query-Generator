import pytest
import os
from flask import Flask
from app import app as flask_app
from database import DatabaseManager
from nlp_service import NLPService
from query_generator import QueryGenerator
from semantic_mapper import SemanticMapper

@pytest.fixture
def app():
    """Create a Flask test client"""
    flask_app.config['TESTING'] = True
    return flask_app

@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()

@pytest.fixture
def db_manager():
    """Create a database manager instance for testing"""
    # Use a test database URL for integration tests
    test_db_url = os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/test_bike_share')
    return DatabaseManager(test_db_url)

@pytest.fixture
def nlp_service():
    """Create an NLP service instance for testing"""
    return NLPService()

@pytest.fixture
def semantic_mapper(db_manager):
    """Create a semantic mapper instance for testing"""
    return SemanticMapper(db_manager)

@pytest.fixture
def query_generator(db_manager, semantic_mapper):
    """Create a query generator instance for testing"""
    return QueryGenerator(db_manager, semantic_mapper)

@pytest.fixture
def sample_trip_data():
    """Sample trip data for testing"""
    return {
        'trip_id': 1001,
        'started_at': '2025-06-01 08:00:00',
        'ended_at': '2025-06-01 08:25:00',
        'start_station_id': 1,
        'end_station_id': 2,
        'bike_id': 1,
        'trip_distance_km': 3.5,
        'rider_birth_year': 1990,
        'rider_gender': 'female'
    }

@pytest.fixture
def sample_station_data():
    """Sample station data for testing"""
    return {
        'station_id': 1,
        'station_name': 'Congress Avenue',
        'latitude': 30.2651,
        'longitude': -97.7456,
        'capacity': 20
    }

@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    return {
        'weather_date': '2025-06-01',
        'high_temp_c': 32.5,
        'low_temp_c': 24.0,
        'precipitation_mm': 0.0
    }

@pytest.fixture
def sample_entities():
    """Sample extracted entities for testing"""
    return {
        'dates': ['june 2025'],
        'locations': ['congress avenue'],
        'time_periods': ['june 2025'],
        'weather_conditions': [],
        'aggregations': ['average'],
        'filters': [],
        'measurements': ['time'],
        'demographics': []
    }
