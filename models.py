"""
Database models representing the bike share schema
These are used for reference and documentation purposes
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List, Dict, Any

@dataclass
class Station:
    station_id: int
    station_name: str
    latitude: Optional[float]
    longitude: Optional[float]
    capacity: Optional[int]

@dataclass
class Bike:
    bike_id: int
    bike_model: Optional[str]
    acquisition_date: Optional[date]
    current_station_id: Optional[int]

@dataclass
class Trip:
    trip_id: int
    bike_id: Optional[int]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    start_station_id: Optional[int]
    end_station_id: Optional[int]
    trip_distance_km: Optional[float]
    rider_birth_year: Optional[int]
    rider_gender: Optional[str]

@dataclass
class DailyWeather:
    weather_date: date
    high_temp_c: Optional[float]
    low_temp_c: Optional[float]
    precipitation_mm: Optional[float]

# Schema metadata for semantic mapping
SCHEMA_METADATA = {
    "tables": {
        "stations": {
            "primary_key": "station_id",
            "columns": {
                "station_id": {"type": "integer", "description": "Unique identifier for bike stations"},
                "station_name": {"type": "varchar", "description": "Name of the bike station location"},
                "latitude": {"type": "numeric", "description": "Geographic latitude coordinate"},
                "longitude": {"type": "numeric", "description": "Geographic longitude coordinate"},
                "capacity": {"type": "integer", "description": "Maximum number of bikes the station can hold"}
            }
        },
        "bikes": {
            "primary_key": "bike_id",
            "columns": {
                "bike_id": {"type": "integer", "description": "Unique identifier for bikes"},
                "bike_model": {"type": "varchar", "description": "Type of bike (classic, electric, cargo)"},
                "acquisition_date": {"type": "date", "description": "Date when the bike was acquired"},
                "current_station_id": {"type": "integer", "description": "Current station where the bike is located"}
            }
        },
        "trips": {
            "primary_key": "trip_id",
            "columns": {
                "trip_id": {"type": "integer", "description": "Unique identifier for trips"},
                "bike_id": {"type": "integer", "description": "ID of the bike used for the trip"},
                "started_at": {"type": "timestamp", "description": "When the trip started"},
                "ended_at": {"type": "timestamp", "description": "When the trip ended"},
                "start_station_id": {"type": "integer", "description": "Station where the trip began"},
                "end_station_id": {"type": "integer", "description": "Station where the trip ended"},
                "trip_distance_km": {"type": "numeric", "description": "Distance traveled in kilometers"},
                "rider_birth_year": {"type": "integer", "description": "Birth year of the rider"},
                "rider_gender": {"type": "varchar", "description": "Gender of the rider (male, female, non-binary)"}
            }
        },
        "daily_weather": {
            "primary_key": "weather_date",
            "columns": {
                "weather_date": {"type": "date", "description": "Date of weather observation"},
                "high_temp_c": {"type": "numeric", "description": "Highest temperature in Celsius"},
                "low_temp_c": {"type": "numeric", "description": "Lowest temperature in Celsius"},
                "precipitation_mm": {"type": "numeric", "description": "Precipitation amount in millimeters"}
            }
        }
    }
}
