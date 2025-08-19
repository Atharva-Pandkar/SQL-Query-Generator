import pytest
from flask import json

def test_index_route(client):
    """Test the main page route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Bike Share Analytics' in response.data

def test_query_endpoint_valid_request(client):
    """Test query endpoint with valid request"""
    data = {
        'question': 'What was the average ride time for journeys that started at Congress Avenue in June 2025?'
    }
    response = client.post('/query',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'sql' in result
    assert 'result' in result
    assert result.get('error') is None

def test_query_endpoint_empty_question(client):
    """Test query endpoint with empty question"""
    data = {'question': ''}
    response = client.post('/query',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result.get('error') is not None

def test_query_endpoint_missing_question(client):
    """Test query endpoint with missing question field"""
    data = {}
    response = client.post('/query',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result.get('error') is not None

def test_query_endpoint_invalid_json(client):
    """Test query endpoint with invalid JSON"""
    response = client.post('/query',
                          data='invalid json',
                          content_type='application/json')
    assert response.status_code == 400
    result = json.loads(response.data)
    assert result.get('error') is not None

def test_health_check_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['status'] == 'healthy'
    assert result['database'] == 'connected'

def test_query_endpoint_error_handling(client, monkeypatch):
    """Test query endpoint error handling"""
    # Mock the query generator to raise an exception
    def mock_generate_query(*args):
        raise Exception("Test error")
    
    from query_generator import QueryGenerator
    monkeypatch.setattr(QueryGenerator, 'generate_query', mock_generate_query)
    
    data = {
        'question': 'What was the average ride time?'
    }
    response = client.post('/query',
                          data=json.dumps(data),
                          content_type='application/json')
    assert response.status_code == 500
    result = json.loads(response.data)
    assert result.get('error') is not None
