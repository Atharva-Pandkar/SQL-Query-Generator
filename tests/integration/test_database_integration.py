import pytest
from database import DatabaseManager

class TestDatabaseIntegration:
    """Integration tests for database operations"""

    def test_schema_validation(self, db_manager):
        """Test that the database schema matches expected structure"""
        schema = db_manager.get_schema_info()
        
        # Verify required tables exist
        assert 'trips' in schema
        assert 'stations' in schema
        assert 'bikes' in schema
        assert 'daily_weather' in schema
        
        # Verify trips table structure
        trips = schema['trips']
        assert any(col['name'] == 'trip_id' for col in trips['columns'])
        assert any(col['name'] == 'started_at' for col in trips['columns'])
        assert any(col['name'] == 'rider_gender' for col in trips['columns'])
        
        # Verify stations table structure
        stations = schema['stations']
        assert any(col['name'] == 'station_id' for col in stations['columns'])
        assert any(col['name'] == 'station_name' for col in stations['columns'])

    def test_query_execution(self, db_manager):
        """Test executing various types of queries"""
        # Test simple SELECT
        result = db_manager.execute_query(
            "SELECT COUNT(*) as count FROM trips"
        )
        assert result is not None
        assert len(result) == 1
        assert 'count' in result[0]
        
        # Test parameterized query
        result = db_manager.execute_query(
            "SELECT * FROM trips WHERE rider_gender = %s LIMIT 1",
            ['female']
        )
        assert result is not None
        if len(result) > 0:
            assert 'trip_id' in result[0]
            assert 'rider_gender' in result[0]

    def test_complex_joins(self, db_manager):
        """Test complex queries with multiple joins"""
        query = """
        SELECT 
            s.station_name,
            COUNT(t.trip_id) as trip_count,
            AVG(t.trip_distance_km) as avg_distance
        FROM trips t
        JOIN stations s ON t.start_station_id = s.station_id
        JOIN daily_weather w ON DATE(t.started_at) = w.weather_date
        WHERE w.precipitation_mm > 0
        GROUP BY s.station_name
        LIMIT 5
        """
        
        result = db_manager.execute_query(query)
        assert result is not None
        if len(result) > 0:
            assert 'station_name' in result[0]
            assert 'trip_count' in result[0]
            assert 'avg_distance' in result[0]

    def test_transaction_rollback(self, db_manager):
        """Test transaction management and rollback"""
        # Start transaction
        db_manager.cursor.execute("BEGIN")
        
        try:
            # Execute invalid query to trigger rollback
            db_manager.execute_query("SELECT * FROM nonexistent_table")
        except Exception:
            # Ensure transaction is rolled back
            db_manager.cursor.execute("ROLLBACK")
        
        # Verify we can still execute queries
        result = db_manager.execute_query("SELECT 1 as test")
        assert result is not None
        assert result[0]['test'] == 1

    def test_concurrent_connections(self):
        """Test handling multiple database connections"""
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        
        # Execute queries on both connections
        result1 = db1.execute_query("SELECT COUNT(*) as count FROM trips")
        result2 = db2.execute_query("SELECT COUNT(*) as count FROM stations")
        
        assert result1 is not None
        assert result2 is not None
        
        # Clean up
        db1.close()
        db2.close()

    def test_error_conditions(self, db_manager):
        """Test various error conditions"""
        # Test invalid SQL
        with pytest.raises(Exception):
            db_manager.execute_query("INVALID SQL")
        
        # Test invalid parameters
        with pytest.raises(Exception):
            db_manager.execute_query(
                "SELECT * FROM trips WHERE trip_id = %s",
                ['invalid']  # Should be integer
            )
        
        # Test too many parameters
        with pytest.raises(Exception):
            db_manager.execute_query(
                "SELECT * FROM trips WHERE trip_id = %s",
                [1, 2]  # Too many parameters
            )
