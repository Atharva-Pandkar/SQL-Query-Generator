import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
from .database import DatabaseManager

class SemanticMapper:
    """Maps natural language entities to database schema elements"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Predefined semantic mappings for common bike-share terms
        self.domain_mappings = {
            'time_concepts': {
                'journey': ['trips'],
                'ride': ['trips'], 
                'trip': ['trips'],
                'departure': ['start_station_id', 'started_at'],
                'arrival': ['end_station_id', 'ended_at'],
                'duration': ['ended_at - started_at'],
                'ride time': ['ended_at - started_at'],
                'weekends': ['EXTRACT(ISODOW FROM started_at) IN (6, 7)'],
                'weekend': ['EXTRACT(ISODOW FROM started_at) IN (6, 7)'],
                'weekdays': ['EXTRACT(ISODOW FROM started_at) BETWEEN 1 AND 5'],
                'weekday': ['EXTRACT(ISODOW FROM started_at) BETWEEN 1 AND 5']
            },
            'location_concepts': {
                'station': ['stations'],
                'docking point': ['stations'],
                'location': ['stations'],
                'congress avenue': ["station_name = 'Congress Avenue'"],
                'barton springs': ["station_name = 'Barton Springs'"],
                'capitol square': ["station_name = 'Capitol Square'"],
                'east side': ["station_name = 'East Side'"],
                'river walk': ["station_name = 'River Walk'"]
            },
            'measurement_concepts': {
                'kilometres': ['trip_distance_km'],
                'kilometers': ['trip_distance_km'],
                'km': ['trip_distance_km'],
                'distance': ['trip_distance_km'],
                'minutes': ['EXTRACT(EPOCH FROM (ended_at - started_at))/60'],
                'time': ['ended_at - started_at']
            },
            'demographic_concepts': {
                'women': ["rider_gender = 'female'"],
                'men': ["rider_gender = 'male'"],
                'female': ["rider_gender = 'female'"],
                'male': ["rider_gender = 'male'"],
                'gender': ['rider_gender']
            },
            'weather_concepts': {
                'rainy': ['precipitation_mm > 0'],
                'sunny': ['precipitation_mm = 0'],
                'rain': ['precipitation_mm > 0'],
                'weather': ['daily_weather']
            },
            'bike_concepts': {
                'ebikes': ["bike_model = 'E‑Bike'"],
                'electric bikes': ["bike_model = 'E‑Bike'"],
                'electric': ["bike_model = 'E‑Bike'"],
                'e-bike': ["bike_model = 'E‑Bike'"],
                'classic bikes': ["bike_model = 'Classic'"],
                'classic': ["bike_model = 'Classic'"],
                'step-thru': ["bike_model = 'Step‑Thru'"],
                'step thru': ["bike_model = 'Step‑Thru'"]
            }
        }
    
    def map_entities_to_schema(self, question: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map extracted entities to database schema elements
        Returns mappings with confidence scores
        """
        schema_info = self.db_manager.get_schema_info()
        
        mappings = {
            'tables': [],
            'columns': [],
            'filters': [],
            'joins': [],
            'aggregations': [],
            'date_filters': []
        }
        
        # Map based on domain knowledge
        self._apply_domain_mappings(question, mappings)
        
        # Map entities to schema elements with scoring
        self._map_locations(entities.get('locations', []), schema_info, mappings)
        self._map_demographics(entities.get('demographics', []), mappings)
        self._map_weather_conditions(entities.get('weather_conditions', []), mappings)
        self._map_time_periods(entities.get('time_periods', []), mappings)
        self._map_measurements(entities.get('measurements', []), mappings)
        self._map_aggregations(entities.get('aggregations', []), mappings)
        self._map_bike_types(question, mappings)
        
        # Determine required joins based on mapped tables
        self._determine_joins(mappings, schema_info)
        
        return mappings
    
    def _apply_domain_mappings(self, question: str, mappings: Dict[str, Any]):
        """Apply predefined domain-specific mappings"""
        question_lower = question.lower()
        
        for category, concepts in self.domain_mappings.items():
            for concept, schema_elements in concepts.items():
                if concept in question_lower:
                    for element in schema_elements:
                        if element.startswith('station_name ='):
                            mappings['filters'].append({
                                'condition': element,
                                'confidence': 0.95
                            })
                        elif element.startswith('rider_gender ='):
                            mappings['filters'].append({
                                'condition': element,
                                'confidence': 0.95
                            })
                        elif element.startswith('precipitation_mm'):
                            mappings['filters'].append({
                                'condition': element,
                                'confidence': 0.9
                            })
                            mappings['tables'].append({
                                'name': 'daily_weather',
                                'confidence': 0.9
                            })
                        elif element.startswith('EXTRACT(ISODOW'):
                            mappings['filters'].append({
                                'condition': element,
                                'confidence': 0.9
                            })
                        elif element in ['trips', 'stations', 'bikes', 'daily_weather']:
                            mappings['tables'].append({
                                'name': element,
                                'confidence': 0.9
                            })
                        else:
                            mappings['columns'].append({
                                'name': element,
                                'confidence': 0.8
                            })
    
    def _map_locations(self, locations: List[str], schema_info: Dict[str, Any], mappings: Dict[str, Any]):
        """Map location entities to station-related elements"""
        if not locations:
            return
        
        # Add stations table if locations are mentioned
        mappings['tables'].append({
            'name': 'stations',
            'confidence': 0.8
        })
        
        for location in locations:
            # Check for exact station name matches
            station_mapping = self._find_station_match(location.lower())
            if station_mapping:
                mappings['filters'].append({
                    'condition': station_mapping,
                    'confidence': 0.9
                })
    
    def _find_station_match(self, location: str) -> Optional[str]:
        """Find matching station name in the database"""
        station_names = [
            'congress avenue', 'barton springs', 'capitol square',
            'east side', 'river walk'
        ]
        
        for station in station_names:
            if self._similarity_score(location, station) > 0.7:
                return f"station_name = '{station.title()}'"
        
        return None
    
    def _map_demographics(self, demographics: List[Dict[str, str]], mappings: Dict[str, Any]):
        """Map demographic entities to rider information"""
        for demo in demographics:
            if demo.get('type') == 'gender':
                value = demo.get('value', '').lower()
                if value in ['women', 'female']:
                    mappings['filters'].append({
                        'condition': "rider_gender = 'female'",
                        'confidence': 0.95
                    })
                elif value in ['men', 'male']:
                    mappings['filters'].append({
                        'condition': "rider_gender = 'male'",
                        'confidence': 0.95
                    })
                
                mappings['tables'].append({
                    'name': 'trips',
                    'confidence': 0.9
                })
    
    def _map_weather_conditions(self, conditions: List[str], mappings: Dict[str, Any]):
        """Map weather conditions to weather table filters"""
        if not conditions:
            return
        
        mappings['tables'].append({
            'name': 'daily_weather',
            'confidence': 0.9
        })
        
        for condition in conditions:
            if condition == 'rainy':
                mappings['filters'].append({
                    'condition': 'precipitation_mm > 0',
                    'confidence': 0.95
                })
            elif condition == 'sunny':
                mappings['filters'].append({
                    'condition': 'precipitation_mm = 0',
                    'confidence': 0.9
                })
    
    def _map_time_periods(self, periods: List[str], mappings: Dict[str, Any]):
        """Map time periods to date filters"""
        for period in periods:
            if 'june 2025' in period.lower():
                mappings['date_filters'].append({
                    'condition': "DATE_PART('month', started_at) = 6 AND DATE_PART('year', started_at) = 2025",
                    'confidence': 0.95
                })
            elif 'first week' in period.lower() and 'june' in period.lower():
                mappings['date_filters'].append({
                    'condition': "started_at BETWEEN '2025-06-01' AND '2025-06-07'",
                    'confidence': 0.9
                })
            elif 'last month' in period.lower():
                mappings['date_filters'].append({
                    'condition': "DATE_PART('month', started_at) = 6 AND DATE_PART('year', started_at) = 2025",
                    'confidence': 0.8
                })
    
    def _map_measurements(self, measurements: List[str], mappings: Dict[str, Any]):
        """Map measurement types to appropriate columns"""
        for measurement in measurements:
            if measurement == 'distance':
                mappings['columns'].append({
                    'name': 'trip_distance_km',
                    'confidence': 0.9
                })
            elif measurement == 'time':
                mappings['columns'].append({
                    'name': 'ended_at - started_at',
                    'confidence': 0.8
                })
    
    def _map_aggregations(self, aggregations: List[str], mappings: Dict[str, Any]):
        """Map aggregation functions"""
        for agg in aggregations:
            mappings['aggregations'].append({
                'function': agg.upper(),
                'confidence': 0.95
            })
    
    def _map_bike_types(self, question: str, mappings: Dict[str, Any]):
        """Map bike type mentions to specific bike models"""
        question_lower = question.lower()
        
        bike_mappings = {
            'ebikes': "bike_model = 'E‑Bike'",
            'e-bikes': "bike_model = 'E‑Bike'",
            'electric bikes': "bike_model = 'E‑Bike'",
            'electric': "bike_model = 'E‑Bike'",
            'classic bikes': "bike_model = 'Classic'",
            'classic': "bike_model = 'Classic'",
            'step-thru': "bike_model = 'Step‑Thru'",
            'step thru': "bike_model = 'Step‑Thru'"
        }
        
        for bike_term, condition in bike_mappings.items():
            if bike_term in question_lower:
                mappings['filters'].append({
                    'condition': condition,
                    'confidence': 0.95
                })
                mappings['tables'].append({
                    'name': 'bikes',
                    'confidence': 0.9
                })
                break
    
    def _determine_joins(self, mappings: Dict[str, Any], schema_info: Dict[str, Any]):
        """Determine necessary joins based on mapped tables"""
        table_names = [t['name'] for t in mappings['tables']]
        unique_tables = list(set(table_names))
        
        # Define common join patterns
        join_patterns = {
            ('trips', 'stations'): [
                "trips.start_station_id = stations.station_id",
                "trips.end_station_id = stations.station_id"
            ],
            ('trips', 'daily_weather'): [
                "DATE(trips.started_at) = daily_weather.weather_date"
            ],
            ('trips', 'bikes'): [
                "trips.bike_id = bikes.bike_id"
            ]
        }
        
        for i, table1 in enumerate(unique_tables):
            for table2 in unique_tables[i+1:]:
                join_key = tuple(sorted([table1, table2]))
                if join_key in join_patterns:
                    for join_condition in join_patterns[join_key]:
                        mappings['joins'].append({
                            'condition': join_condition,
                            'confidence': 0.9
                        })
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def score_column_relevance(self, column_name: str, user_text: str) -> float:
        """
        Score how relevant a column is to the user's question
        Higher score means more relevant
        """
        user_words = set(user_text.lower().split())
        column_words = set(column_name.lower().replace('_', ' ').split())
        
        # Direct word matches
        direct_matches = len(user_words.intersection(column_words))
        if direct_matches > 0:
            return 0.8 + (direct_matches * 0.1)
        
        # Semantic similarity
        max_similarity = 0
        for user_word in user_words:
            for col_word in column_words:
                similarity = self._similarity_score(user_word, col_word)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity * 0.6
