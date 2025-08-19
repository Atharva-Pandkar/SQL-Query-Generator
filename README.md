# Bike Share Analytics Assistant

A natural language interface for querying bike-share data using NLP and LLMs. Users can ask questions in plain English, and the system converts them into optimized SQL queries.

## Table of Contents
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Environment Setup](#environment-setup)
- [Database Schema](#database-schema)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Development Guidelines](#development-guidelines)

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd atri_lt
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

4. Set up environment variables in `.env`:
```env
# Database Configuration
DB_HOST=your_host
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Flask Configuration
FLASK_ENV=development
FLASK_APP=app.py
SECRET_KEY=your_secret_key

# Test Database (for running tests)
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/test_bike_share
```

5. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Architecture

### Core Components

1. **Web Interface (`app.py`)**
   - Flask web application
   - Handles HTTP requests
   - Manages user sessions
   - Routes queries to appropriate services

2. **Database Manager (`database.py`)**
   - Manages PostgreSQL connections
   - Executes parameterized SQL queries
   - Provides schema introspection
   - Implements connection pooling and retry logic

3. **NLP Service (`nlp_service.py`)**
   - Uses spaCy for Named Entity Recognition
   - Extracts key entities from user queries:
     - Dates and times
     - Locations
     - Demographics
     - Weather conditions
     - Aggregation functions

4. **Semantic Mapper (`semantic_mapper.py`)**
   - Maps natural language concepts to database schema
   - Handles entity resolution
   - Manages domain-specific vocabulary
   - Provides context for query generation

5. **Query Generator (`query_generator.py`)**
   - Uses OpenAI GPT-4 for SQL generation
   - Implements SQL safety checks
   - Handles query parameterization
   - Manages query optimization

### Query Processing Pipeline

1. User submits natural language question
2. NLP Service extracts entities and intent
3. Semantic Mapper translates to database concepts
4. Query Generator creates SQL with GPT-4
5. Database Manager executes and returns results

## Database Schema

### Core Tables

1. **stations**
   - station_id (PK)
   - station_name
   - latitude
   - longitude
   - capacity

2. **bikes**
   - bike_id (PK)
   - bike_model
   - acquisition_date
   - current_station_id (FK)

3. **trips**
   - trip_id (PK)
   - bike_id (FK)
   - started_at
   - ended_at
   - start_station_id (FK)
   - end_station_id (FK)
   - trip_distance_km
   - rider_birth_year
   - rider_gender

4. **daily_weather**
   - weather_date (PK)
   - high_temp_c
   - low_temp_c
   - precipitation_mm

## Running Tests

The project uses pytest for testing. Tests are organized into:
- Unit tests
- Integration tests
- Acceptance tests

### Running All Tests
```bash
pytest
```

### Running Specific Test Categories
```bash
# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage report
pytest --cov=. tests/

# Run specific test file
pytest tests/unit/test_app.py
```

### Test Database Setup
1. Create a test database:
```sql
CREATE DATABASE test_bike_share;
```

2. Apply schema migrations to test database
3. Add test data using provided fixtures

## API Documentation

### Main Endpoint: `/query`

**POST** `/query`
```json
{
    "question": "How many bikes were used on rainy days in June 2025?"
}
```

Response:
```json
{
    "sql": "Generated SQL query",
    "result": "Query results",
    "error": null
}
```

### Health Check: `/health`

**GET** `/health`
```json
{
    "status": "healthy",
    "database": "connected"
}
```

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Implement proper error handling

### Security
- Use parameterized queries
- Validate user input
- Implement rate limiting
- Follow OWASP guidelines

### Testing
- Write tests for new features
- Maintain test coverage
- Use meaningful test names
- Follow AAA pattern (Arrange, Act, Assert)

### Git Workflow
- Use feature branches
- Write meaningful commit messages
- Review code before merging
- Keep PRs focused and small

## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   - Check connection string
   - Verify network connectivity
   - Ensure proper credentials

2. **OpenAI API Errors**
   - Verify API key
   - Check rate limits
   - Handle timeouts

3. **NLP Processing Issues**
   - Verify spaCy model installation
   - Check input text encoding
   - Monitor memory usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request
