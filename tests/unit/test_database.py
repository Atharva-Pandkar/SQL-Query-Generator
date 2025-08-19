import pytest
from unittest.mock import Mock, patch
from database import DatabaseManager

class TestDatabaseManager:
    """Unit tests for DatabaseManager class"""

    @pytest.fixture
    def db_manager(self):
        """Create a DatabaseManager instance with a mock connection"""
        with patch('database.psycopg2') as mock_psycopg2:
            # Mock the connection and cursor
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_psycopg2.connect.return_value = mock_conn
            
            db_manager = DatabaseManager()
            db_manager.conn = mock_conn
            db_manager.cursor = mock_cursor
            return db_manager

    def test_execute_query_select(self, db_manager):
        """Test executing a SELECT query"""
        # Mock the cursor's fetchall method
        expected_result = [{'id': 1, 'name': 'Test'}]
        db_manager.cursor.fetchall.return_value = [(1, 'Test')]
        db_manager.cursor.description = [
            Mock(name='id'),
            Mock(name='name')
        ]

        result = db_manager.execute_query("SELECT * FROM test")
        
        assert result == expected_result
        db_manager.cursor.execute.assert_called_once()

    def test_execute_query_with_params(self, db_manager):
        """Test executing a query with parameters"""
        query = "SELECT * FROM trips WHERE rider_gender = %s"
        params = ['female']
        
        db_manager.execute_query(query, params)
        
        db_manager.cursor.execute.assert_called_with(query, params)

    def test_execute_query_error(self, db_manager):
        """Test handling of database errors"""
        db_manager.cursor.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            db_manager.execute_query("SELECT * FROM nonexistent_table")

    def test_get_schema_info(self, db_manager):
        """Test retrieving schema information"""
        # Mock cursor response for schema query
        mock_schema = [
            ('trips', 'trip_id', 'integer', False),
            ('trips', 'started_at', 'timestamp', True),
            ('stations', 'station_id', 'integer', False),
            ('stations', 'station_name', 'varchar', False)
        ]
        db_manager.cursor.fetchall.return_value = mock_schema

        schema_info = db_manager.get_schema_info()
        
        assert 'trips' in schema_info
        assert 'stations' in schema_info
        assert len(schema_info['trips']['columns']) > 0
        assert len(schema_info['stations']['columns']) > 0

    def test_test_connection(self, db_manager):
        """Test database connection check"""
        db_manager.test_connection()
        db_manager.cursor.execute.assert_called_with("SELECT 1")

    def test_connection_error(self):
        """Test handling of connection errors"""
        with patch('database.psycopg2.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                DatabaseManager().test_connection()

    def test_close_connection(self, db_manager):
        """Test closing database connection"""
        db_manager.close()
        
        db_manager.cursor.close.assert_called_once()
        db_manager.conn.close.assert_called_once()

    def test_validate_table_access(self, db_manager):
        """Test table access validation"""
        # Test allowed tables
        assert db_manager.validate_table_access("SELECT * FROM trips") is True
        assert db_manager.validate_table_access("SELECT * FROM stations") is True
        
        # Test forbidden tables
        assert db_manager.validate_table_access("SELECT * FROM users") is False
        assert db_manager.validate_table_access("SELECT * FROM sensitive_data") is False
