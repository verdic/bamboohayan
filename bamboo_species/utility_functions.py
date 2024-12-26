import re
from django.shortcuts import get_object_or_404

def parse_coordinates(coordinate):
    pattern = r"(\d+\.\d+)[°N|°S]\s(\d+\.\d+)[°E|°W]\s(\d+)(Ft|ft|m|M)"
    match = re.match(pattern, coordinate.strip())
    if not match:
        raise ValueError("Invalid coordinate format.")
    
    latitude = float(match.group(1))
    longitude = float(match.group(2))
    elevation = float(match.group(3))

    # Convert elevation to meters if it's in feet
    if match.group(4).lower() == 'ft':
        elevation *= 0.3048

    return latitude, longitude, elevation
