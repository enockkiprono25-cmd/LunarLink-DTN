"""
LunarLink - Solar Geometry Calculations

Calculates the Sun's apparent direction from a lunar surface site.

Outputs:
- Solar azimuth
- Solar elevation
- Sun-to-site distance
- Geometric horizon visibility

Limitations:
- No terrain-shadow modelling.
- No atmospheric refraction.
- No solar-panel orientation or power calculation.
- Uses the lunar radii supplied by the loaded SPICE constants kernel.
"""

import math
import numbers

import spiceypy as spice

from calculations.coordinates import (
    validate_lunar_coordinates,
    lunar_lat_lon_to_unit_vector,
)

from calculations.spice_geometry import (
    load_kernel_set,
    unload_kernel_set,
)


def _validate_altitude(altitude_km):
    """Validate site altitude above the reference lunar surface."""

    if isinstance(altitude_km, bool) or not isinstance(
        altitude_km, numbers.Real
    ):
        raise TypeError("Altitude must be a real numeric value.")

    if not math.isfinite(altitude_km):
        raise ValueError("Altitude must be finite.")

    if altitude_km < 0:
        raise ValueError("Altitude cannot be negative.")


def _normalize(vector):
    """Return a normalized three-dimensional vector."""

    magnitude = math.sqrt(sum(component ** 2 for component in vector))

    if magnitude == 0:
        raise ValueError("Cannot normalize a zero-length vector.")

    return tuple(component / magnitude for component in vector)


def _dot(first, second):
    """Calculate the dot product of two vectors."""

    return sum(a * b for a, b in zip(first, second))


def _cross(first, second):
    """Calculate the cross product of two vectors."""

    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _calculate_site_position(latitude, longitude, radii, altitude_km):
    """
    Calculate the lunar site position and local reference directions.

    Latitude and longitude are planetocentric and east-positive.
    The coordinate frame must match the supplied coordinates.
    """

    direction = lunar_lat_lon_to_unit_vector(
        latitude,
        longitude,
    )

    a, b, c = radii

    denominator = math.sqrt(
        (direction["x"] / a) ** 2
        + (direction["y"] / b) ** 2
        + (direction["z"] / c) ** 2
    )

    surface_radius = 1.0 / denominator

    surface_position = (
        surface_radius * direction["x"],
        surface_radius * direction["y"],
        surface_radius * direction["z"],
    )

    # Surface normal of the reference ellipsoid.
    normal = _normalize((
        surface_position[0] / (a ** 2),
        surface_position[1] / (b ** 2),
        surface_position[2] / (c ** 2),
    ))

    # Local east direction.
    longitude_rad = math.radians(longitude)

    east = (
        -math.sin(longitude_rad),
        math.cos(longitude_rad),
        0.0,
    )

    # Local north direction.
    north = _normalize(_cross(normal, east))

    # Local up direction.
    up = normal

    # Apply altitude along the ellipsoid surface normal.
    site_position = tuple(
        surface_position[i] + altitude_km * up[i]
        for i in range(3)
    )

    return site_position, east, north, up


def calculate_solar_geometry(
    latitude,
    longitude,
    utc,
    kernel_paths,
    frame="MOON_ME",
    altitude_km=0.0,
):
    """
    Calculate solar geometry at a lunar surface location.

    Args:
        latitude: Planetocentric latitude in degrees.
        longitude: East-positive longitude in degrees.
        utc: UTC timestamp accepted by SPICE.
        kernel_paths: Explicit collection of SPICE kernel paths.
        frame: Lunar body-fixed reference frame.
        altitude_km: Altitude above the reference surface.

    Returns:
        Dictionary containing solar geometry and provenance.
    """

    validate_lunar_coordinates(latitude, longitude)
    _validate_altitude(altitude_km)

    if not isinstance(utc, str) or not utc.strip():
        raise ValueError("UTC must be a non-empty string.")

    if not isinstance(frame, str) or not frame.strip():
        raise ValueError("Reference frame must be a non-empty string.")

    loaded = []

    try:
        # Load kernels through LunarLink's ownership manager.
        loaded = load_kernel_set(kernel_paths)

        # Confirm that SPICE recognizes the requested frame.
        if spice.namfrm(frame) == 0:
            raise ValueError(
                f"SPICE does not recognize reference frame: {frame}"
            )

        # Convert UTC into SPICE ephemeris time.
        et = spice.str2et(utc)

        # Retrieve lunar reference radii.
        dimension, radii_array = spice.bodvrd(
            "MOON",
            "RADII",
            3,
        )

        if dimension != 3:
            raise ValueError("SPICE did not return three lunar radii.")

        radii = tuple(float(value) for value in radii_array)

        # Calculate lunar site position and local directions.
        site_position, east, north, up = _calculate_site_position(
            latitude,
            longitude,
            radii,
            altitude_km,
        )

        # Obtain Sun position relative to the Moon.
        sun_state, _ = spice.spkezr(
            "SUN",
            et,
            frame,
            "NONE",
            "MOON",
        )

        sun_position = tuple(float(value) for value in sun_state[:3])

        # Calculate Sun position relative to the surface site.
        sun_from_site = tuple(
            sun_position[i] - site_position[i]
            for i in range(3)
        )

        sun_distance = math.sqrt(
            sum(value ** 2 for value in sun_from_site)
        )

        sun_direction = _normalize(sun_from_site)

        # Resolve the solar direction into local east/north/up.
        east_component = _dot(sun_direction, east)
        north_component = _dot(sun_direction, north)
        up_component = _dot(sun_direction, up)

        horizontal_component = math.hypot(
            east_component,
            north_component,
        )

        # Solar elevation above the local geometric horizon.
        elevation = math.degrees(
            math.atan2(up_component, horizontal_component)
        )

        # Solar azimuth measured clockwise from north.
        if horizontal_component < 1e-12:
            azimuth = None
        else:
            azimuth = (
                math.degrees(
                    math.atan2(east_component, north_component)
                )
                % 360.0
            )

        return {
            "latitude_deg": float(latitude),
            "longitude_deg": float(longitude),
            "altitude_km": float(altitude_km),
            "utc": utc,
            "et": float(et),
            "frame": frame,
            "lunar_radii_km": radii,
            "site_position_km": site_position,
            "sun_position_moon_centered_km": sun_position,
            "sun_distance_site_km": sun_distance,
            "solar_azimuth_deg": azimuth,
            "solar_elevation_deg": elevation,
            "geometric_horizon_visible": elevation > 0.0,
            "terrain_shadows_modelled": False,
            "kernel_paths": [str(path) for path in loaded],
        }

    finally:
        # Unload only kernels owned by this calculation.
        if loaded:
            unload_kernel_set(loaded)