import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()
from .database import DatabaseManager
from .nlp_service import NLPService
from .query_generator import QueryGenerator
from .semantic_mapper import SemanticMapper

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
# app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize services
db_manager = DatabaseManager()
nlp_service = NLPService()
semantic_mapper = SemanticMapper(db_manager)
query_generator = QueryGenerator(db_manager, semantic_mapper)

@app.route('/')
def index():
    """Render the main chat interface"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    """
    Main endpoint for processing natural language queries
    Accepts: {"question": "<user-text>"}
    Returns: {"sql": "<final-query>", "result": <rows | scalar>, "error": <null | "message">}
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "sql": None,
                "result": None,
                "error": "Request must be JSON"
            }), 400
        
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                "sql": None,
                "result": None,
                "error": "Question is required"
            }), 400
        
        # Extract entities using NER
        entities = nlp_service.extract_entities(question)
        logging.debug(f"Extracted entities: {entities}")
        
        # Generate SQL query using LLM
        sql_result = query_generator.generate_query(question, entities)
        
        if sql_result.get('error'):
            # Make error messages more user-friendly
            error_msg = sql_result['error']
            if "unknown table" in error_msg.lower():
                user_friendly_error = "I couldn't understand your question properly. Try asking about bike trips, stations, or weather data."
            elif "llm failed" in error_msg.lower():
                user_friendly_error = "I had trouble processing your question. Please try rephrasing it or ask about specific bike share data like trip counts or station usage."
            elif "column" in error_msg.lower() and "does not exist" in error_msg.lower():
                user_friendly_error = "I couldn't find the data you're looking for. Try asking about bike trips, station locations, or usage patterns."
            else:
                user_friendly_error = "I couldn't process your question. Please try asking about bike share trips, stations, or usage data."
            
            return jsonify({
                "sql": sql_result.get('sql'),
                "result": None,
                "error": user_friendly_error
            })
        
        # Execute the query
        sql_query = sql_result['sql']
        params = sql_result.get('params', [])
        
        result = db_manager.execute_query(sql_query, params)
        
        # Handle empty results with user-friendly messages
        if not result or (isinstance(result, list) and len(result) == 0):
            return jsonify({
                "sql": sql_query,
                "result": None,
                "error": "No data found matching your criteria. Try asking about available bikes, trips, or stations."
            })
        
        # Format result based on query type
        if isinstance(result, list) and len(result) == 1 and len(result[0]) == 1:
            # Single scalar value
            value = list(result[0].values())[0]
            # Handle None/null results
            if value is None:
                return jsonify({
                    "sql": sql_query,
                    "result": None,
                    "error": "No data found matching your criteria. Try asking about available bikes, trips, or stations."
                })
            # Handle timedelta objects for ride time calculations
            if hasattr(value, 'total_seconds'):
                formatted_result = round(value.total_seconds() / 60, 1)  # Convert to minutes
            else:
                formatted_result = value
        else:
            # Multiple rows or multiple columns
            formatted_result = []
            if result:
                for row in result:
                    formatted_row = {}
                    for key, value in row.items():
                        # Handle timedelta objects
                        if hasattr(value, 'total_seconds'):
                            formatted_row[key] = round(value.total_seconds() / 60, 1)
                        else:
                            formatted_row[key] = value
                    formatted_result.append(formatted_row)
        
        return jsonify({
            "sql": sql_query,
            "result": formatted_result,
            "error": None
        })
        
    except Exception as e:
        logging.error(f"Query processing error: {str(e)}")
        return jsonify({
            "sql": None,
            "result": None,
            "error": "Sorry, I couldn't process your question. Please try asking about bike trips, station usage, or weather data."
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        db_manager.test_connection()
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
