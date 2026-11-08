"""
LunarLink - Lunar Coordinate Utilities

Purpose:
1. Validate lunar latitude and longitude.
2. Convert spherical lunar coordinates into a Moon-centred
   unit direction vector.

Coordinate convention:
- Latitude: planetocentric, degrees.
- Longitude: east-positive, degrees.
- Longitude range: -180 to +180 degrees.
- Latitude range: -90 to +90 degrees.

This module does not calculate astronomical positions,
physical distances, or SPICE reference-frame transformations.
"""

import math
import numbers


def validate_lunar_coordinates(latitude, longitude):
    """
    Validate lunar latitude and longitude.

    Returns:
        True if both coordinates are valid.

    Raises:
        TypeError: If coordinates are not real numeric values.
        ValueError: If coordinates are non-finite or out of range.
    """

    for name, value in (
        ("Latitude", latitude),
        ("Longitude", longitude),
    ):

        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise TypeError(f"{name} must be a real numeric value.")

        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    return True


def lunar_lat_lon_to_unit_vector(latitude, longitude):
    """
    Convert spherical lunar coordinates into a unit direction vector.

    Returns:
        Dictionary containing x, y and z components.

    Note:
        This is a mathematical spherical-coordinate conversion.
        It does not establish a verified lunar body-fixed frame.
    """

    validate_lunar_coordinates(latitude, longitude)

    lat_rad = math.radians(latitude)
    lon_rad = math.radians(longitude)

    x = math.cos(lat_rad) * math.cos(lon_rad)
    y = math.cos(lat_rad) * math.sin(lon_rad)
    z = math.sin(lat_rad)

    # Remove floating-point residuals at the poles.
    if abs(latitude) == 90:
        x = 0.0
        y = 0.0

    return {
        "x": x,
        "y": y,
        "z": z,
    }