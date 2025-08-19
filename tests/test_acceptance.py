import pytest
import requests
import json
import time
from typing import Dict, Any

class TestAcceptance:
    """Acceptance tests for the three public test cases"""
    
    BASE_URL = "http://localhost:5000"
    
    @classmethod
    def setup_class(cls):
        """Wait for server to be ready"""
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.BASE_URL}/health")
                if response.status_code == 200:
                    break
            except requests.ConnectionError:
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    raise Exception("Server not available for testing")
    
    def query_api(self, question: str) -> Dict[str, Any]:
        """Helper method to query the API"""
        response = requests.post(
            f"{self.BASE_URL}/query",
            headers={"Content-Type": "application/json"},
            json={"question": question}
        )
        
        assert response.status_code == 200, f"API call failed: {response.text}"
        return response.json()
    
    def test_t1_average_ride_time_congress_avenue_june_2025(self):
        """
        Test T-1: "What was the average ride time for journeys that started at Congress Avenue in June 2025?"
        Expected answer: 25 minutes
        """
        question = "What was the average ride time for journeys that started at Congress Avenue in June 2025?"
        
        result = self.query_api(question)
        
        # Check that query executed without errors
        assert result.get('error') is None, f"Query failed with error: {result.get('error')}"
        
        # Check that SQL was generated
        assert result.get('sql') is not None, "No SQL query was generated"
        
        # Check the result - should be 25 minutes
        answer = result.get('result')
        assert answer is not None, "No result returned"
        
        # Convert to float for comparison (handle different numeric types)
        if isinstance(answer, (int, float)):
            assert abs(answer - 25) < 0.1, f"Expected 25 minutes, got {answer}"
        else:
            # If it's a more complex result structure, extract the value
            pytest.fail(f"Unexpected result format: {answer}")
    
    def test_t2_most_departures_first_week_june_2025(self):
        """
        Test T-2: "Which docking point saw the most departures during the first week of June 2025?"
        Expected answer: Congress Avenue
        """
        question = "Which docking point saw the most departures during the first week of June 2025?"
        
        result = self.query_api(question)
        
        # Check that query executed without errors
        assert result.get('error') is None, f"Query failed with error: {result.get('error')}"
        
        # Check that SQL was generated
        assert result.get('sql') is not None, "No SQL query was generated"
        
        # Check the result - should be "Congress Avenue"
        answer = result.get('result')
        assert answer is not None, "No result returned"
        
        # Handle different result formats
        if isinstance(answer, str):
            assert "Congress Avenue" in answer, f"Expected 'Congress Avenue', got '{answer}'"
        elif isinstance(answer, list) and len(answer) > 0:
            # If result is a list of rows, check the first row
            first_row = answer[0]
            if isinstance(first_row, dict):
                # Find the station name in the row
                station_found = False
                for key, value in first_row.items():
                    if "Congress Avenue" in str(value):
                        station_found = True
                        break
                assert station_found, f"Expected 'Congress Avenue' in result: {first_row}"
            else:
                assert "Congress Avenue" in str(first_row), f"Expected 'Congress Avenue', got {first_row}"
        else:
            pytest.fail(f"Unexpected result format: {answer}")
    
    def test_t3_kilometers_women_rainy_days_june_2025(self):
        """
        Test T-3: "How many kilometres were ridden by women on rainy days in June 2025?"
        Expected answer: 6.8 km
        """
        question = "How many kilometres were ridden by women on rainy days in June 2025?"
        
        result = self.query_api(question)
        
        # Check that query executed without errors
        assert result.get('error') is None, f"Query failed with error: {result.get('error')}"
        
        # Check that SQL was generated
        assert result.get('sql') is not None, "No SQL query was generated"
        
        # Check the result - should be 6.8 km
        answer = result.get('result')
        assert answer is not None, "No result returned"
        
        # Convert to float for comparison
        if isinstance(answer, (int, float)):
            assert abs(answer - 6.8) < 0.1, f"Expected 6.8 km, got {answer}"
        else:
            # If it's a more complex result structure, extract the value
            pytest.fail(f"Unexpected result format: {answer}")
    
    def test_api_error_handling(self):
        """Test that API handles errors gracefully"""
        # Test empty question
        response = requests.post(
            f"{self.BASE_URL}/query",
            headers={"Content-Type": "application/json"},
            json={"question": ""}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result.get('error') is not None
    
    def test_api_malformed_request(self):
        """Test handling of malformed requests"""
        # Test non-JSON request
        response = requests.post(
            f"{self.BASE_URL}/query",
            headers={"Content-Type": "text/plain"},
            data="not json"
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result.get('error') is not None
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result.get('status') == 'healthy'
        assert result.get('database') == 'connected'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
