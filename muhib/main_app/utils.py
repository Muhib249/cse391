from math import sin, cos, sqrt, atan2, radians
import requests
from datetime import datetime

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6373.0  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c * 1000  # Convert to meters

def verify_attendance(session, student_lat, student_lon):
    """Verify attendance based on geolocation and session validity."""
    if not session.is_active or datetime.now() > session.expiry_time:
        return False, "Session expired"
    
    if not (session.latitude and session.longitude):
        return False, "Location data not available for this session"
    
    distance = calculate_distance(
        session.latitude, 
        session.longitude,
        student_lat, 
        student_lon
    )
    
    if distance > session.radius:
        return False, f"Location verification failed. You are {distance:.2f} meters away."
    
    return True, "Attendance verified"

def get_device_info(request):
    """Get device information from request"""
    return {
        'ip': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'timestamp': datetime.now()
    }