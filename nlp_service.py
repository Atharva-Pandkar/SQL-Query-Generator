import spacy
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

class NLPService:
    """Natural Language Processing service using spaCy for entity extraction"""
    
    def __init__(self):
        try:
            # Load spaCy English model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model is not installed
            logging.warning("spaCy English model not found, using blank model")
            self.nlp = spacy.blank("en")
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract relevant entities from natural language query
        Returns structured entity information for SQL generation
        """
        doc = self.nlp(text.lower())
        
        entities = {
            'numbers': [],
            'dates': [],
            'locations': [],
            'people': [],
            'organizations': [],
            'time_periods': [],
            'weather_conditions': [],
            'aggregations': [],
            'filters': [],
            'measurements': [],
            'demographics': []
        }
        
        # Extract spaCy named entities
        for ent in doc.ents:
            if ent.label_ in ['CARDINAL', 'QUANTITY']:
                entities['numbers'].append(ent.text)
            elif ent.label_ in ['DATE', 'TIME']:
                entities['dates'].append(ent.text)
            elif ent.label_ in ['GPE', 'LOC', 'FAC']:
                entities['locations'].append(ent.text)
            elif ent.label_ == 'PERSON':
                entities['people'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
        
        # Extract domain-specific patterns
        self._extract_time_patterns(text, entities)
        self._extract_weather_patterns(text, entities)
        self._extract_aggregation_patterns(text, entities)
        self._extract_measurement_patterns(text, entities)
        self._extract_demographic_patterns(text, entities)
        self._extract_location_patterns(text, entities)
        
        return entities
    
    def _extract_time_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract time-related patterns from text"""
        # Date patterns
        date_patterns = [
            r'last month',
            r'this month',
            r'june 2025',
            r'first week of june',
            r'morning',
            r'afternoon',
            r'evening',
            r'night',
            r'weekday',
            r'weekend'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                entities['time_periods'].append(pattern)
        
        # Specific date extraction
        if 'june 2025' in text:
            entities['dates'].append('2025-06')
        if 'first week' in text and 'june' in text:
            entities['dates'].append('2025-06-01 to 2025-06-07')
    
    def _extract_weather_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract weather-related patterns"""
        weather_patterns = {
            'rainy': ['rainy', 'rain', 'wet'],
            'sunny': ['sunny', 'clear', 'dry'],
            'hot': ['hot', 'warm', 'high temperature'],
            'cold': ['cold', 'cool', 'low temperature']
        }
        
        for condition, keywords in weather_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    entities['weather_conditions'].append(condition)
                    break
    
    def _extract_aggregation_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract aggregation operations from text"""
        aggregation_patterns = {
            'count': ['how many', 'count', 'number of'],
            'average': ['average', 'avg', 'mean'],
            'sum': ['total', 'sum', 'add up'],
            'max': ['maximum', 'max', 'highest', 'most'],
            'min': ['minimum', 'min', 'lowest', 'least']
        }
        
        for agg_type, keywords in aggregation_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    entities['aggregations'].append(agg_type)
                    break
    
    def _extract_measurement_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract measurement-related terms"""
        measurements = {
            'distance': ['kilometres', 'kilometers', 'km', 'distance', 'miles'],
            'time': ['minutes', 'hours', 'time', 'duration'],
            'temperature': ['degrees', 'celsius', 'fahrenheit', 'temp'],
            'precipitation': ['mm', 'millimeters', 'rain', 'precipitation']
        }
        
        for measure_type, keywords in measurements.items():
            for keyword in keywords:
                if keyword in text:
                    entities['measurements'].append(measure_type)
                    break
    
    def _extract_demographic_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract demographic information"""
        demographics = {
            'gender': ['women', 'men', 'male', 'female', 'non-binary'],
            'age': ['young', 'old', 'adult', 'senior', 'teen']
        }
        
        for demo_type, keywords in demographics.items():
            for keyword in keywords:
                if keyword in text:
                    entities['demographics'].append({
                        'type': demo_type,
                        'value': keyword
                    })
    
    def _extract_location_patterns(self, text: str, entities: Dict[str, Any]):
        """Extract location-specific patterns"""
        # Look for station names mentioned in the schema
        station_names = [
            'congress avenue', 'barton springs', 'capitol square', 
            'east side', 'river walk'
        ]
        
        for station in station_names:
            if station in text:
                entities['locations'].append(station)
        
        # General location terms
        location_terms = ['station', 'docking point', 'departure', 'arrival']
        for term in location_terms:
            if term in text:
                entities['filters'].append({
                    'type': 'location',
                    'value': term
                })
