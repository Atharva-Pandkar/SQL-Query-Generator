# Test Queries for Bike Share Analytics Assistant

Here are working test queries you can try to verify the system is functioning properly:

## ✅ Working Queries (These should return results)

### Basic Data Exploration
1. **"What bike models are available?"**
   - Expected: Shows Classic, E‑Bike, Step‑Thru

2. **"Show me all trips with their distances"**
   - Expected: List of 10 trips with distances

3. **"How many trips happened in June 2025?"**
   - Expected: Total count of trips

### Location-Based Queries
4. **"Which station had the most departures in the first week of June?"**
   - Expected: Congress Avenue

5. **"What was the average ride time for journeys that started at Congress Avenue in June 2025?"**
   - Expected: 25 minutes

### Weather and Demographics
6. **"How many kilometers did women ride on rainy days in June 2025?"**
   - Expected: 6.8 km

7. **"Show me trips that happened on rainy days"**
   - Expected: List of trips with weather data

### Time-Based Queries
8. **"What trips happened on Monday?"**
   - Expected: Monday trips (1004, 1005)

9. **"Show me weekend trips"**
   - Expected: Sunday trips (1001, 1002, 1003)

## ⚠️ Currently Not Working (Due to Unicode Issues)

### Bike Model Queries (Known Issue)
10. **"What is the average trip distance for ebikes on weekends?"**
    - Current Issue: Unicode character mismatch in bike model names
    - Workaround: Try "What is the average distance for all weekend trips?"

11. **"How many classic bike trips were there?"**
    - Current Issue: Same Unicode problem
    - Workaround: Try "How many trips were there in total?"

## 🔧 Technical Details

The main issue is that bike model names in the database use Unicode character U+2011 (non-breaking hyphen) instead of regular ASCII hyphens:
- Database: "E‑Bike" (with U+2011)
- System expects: "E-Bike" (with ASCII hyphen)

## 📊 Expected Results Summary

- **Total trips**: 10
- **Stations**: 5 locations  
- **Bike models**: 3 types
- **Date range**: June 2025
- **Congress Avenue average ride time**: 25 minutes
- **Women's rainy day distance**: 6.8 km