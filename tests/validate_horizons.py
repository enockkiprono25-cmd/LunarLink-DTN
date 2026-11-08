

"""
LunarLink - Independent JPL Horizons Validation

Compares LunarLink solar geometry against independent
JPL Horizons geometric vectors.

Run:
    python tests/validate_horizons.py

This is an external validation script, not a pytest test.
"""

import csv
import io
import json
import math
import sys
import time

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests
import spiceypy as spice

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from calculations.solar_geometry import calculate_solar_geometry


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

KERNEL_DIR = ROOT / "data" / "spice_kernels"

KERNELS = [
    KERNEL_DIR / "lsk" / "naif0012.tls",
    KERNEL_DIR / "spk" / "de440s.bsp",
    KERNEL_DIR / "pck" / "moon_pa_de440_200625.bpc",
    KERNEL_DIR / "pck" / "pck00011.tpc",
    KERNEL_DIR / "fk" / "moon_de440_250416.tf",
]

FRAME = "MOON_ME"

SITES = [
    ("South Pole", -90.0, 0.0),
    ("Near South Pole", -89.0, 0.0),
    ("High Latitude East", -85.0, 90.0),
    ("High Latitude West", -85.0, -90.0),
    ("Equatorial Reference", 0.0, 0.0),
]

TIMESTAMPS = [
    "2026-11-08T00:00:00",
    "2026-11-08T12:00:00",
    "2026-11-09T00:00:00",
]

# Initial engineering tolerances.
# Review observed differences before treating these
# as final scientific acceptance criteria.

VECTOR_TOLERANCE_KM = 0.05
ANGLE_TOLERANCE_DEG = 0.0001

CACHE_DIR = ROOT / "data" / "validation"
CACHE_FILE = CACHE_DIR / "horizons_cache.json"

REPORT_DIR = ROOT / "reports" / "validation"
REPORT_FILE = REPORT_DIR / "horizons_validation_latest.json"


# --------------------------------------------------
# MATHEMATICAL UTILITIES
# --------------------------------------------------

def normalize(vector):
    vector = np.asarray(vector, dtype=float)
    magnitude = np.linalg.norm(vector)

    if magnitude == 0:
        raise ValueError("Cannot normalize zero-length vector.")

    return vector / magnitude


def angular_difference_deg(first, second):
    """Stable angular separation between two vectors."""

    first = normalize(first)
    second = normalize(second)

    cross_magnitude = np.linalg.norm(np.cross(first, second))
    dot_product = np.dot(first, second)

    return math.degrees(
        math.atan2(cross_magnitude, dot_product)
    )


def calculate_local_basis(latitude, longitude, radii):
    """Construct local east, north and up directions."""

    lat = math.radians(latitude)
    lon = math.radians(longitude)

    direction = np.array([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat),
    ])

    a, b, c = radii

    denominator = math.sqrt(
        (direction[0] / a) ** 2
        + (direction[1] / b) ** 2
        + (direction[2] / c) ** 2
    )

    surface_radius = 1.0 / denominator
    surface_position = surface_radius * direction

    up = normalize(np.array([
        surface_position[0] / a**2,
        surface_position[1] / b**2,
        surface_position[2] / c**2,
    ]))

    east = np.array([
        -math.sin(lon),
        math.cos(lon),
        0.0,
    ])

    north = normalize(np.cross(up, east))

    return east, north, up


def calculate_solar_angles(vector, east, north, up):

    direction = normalize(vector)

    e = float(np.dot(direction, east))
    n = float(np.dot(direction, north))
    u = float(np.dot(direction, up))

    horizontal = math.hypot(e, n)

    elevation = math.degrees(
        math.atan2(u, horizontal)
    )

    azimuth = None

    if horizontal >= 1e-12:
        azimuth = (
            math.degrees(math.atan2(e, n)) % 360.0
        )

    return elevation, azimuth


def azimuth_difference(first, second):

    if first is None or second is None:
        return None

    difference = abs(first - second)

    return min(difference, 360.0 - difference)


# --------------------------------------------------
# HORIZONS DATA RETRIEVAL
# --------------------------------------------------

def query_horizons(latitude, longitude, utc):

    horizons_time = utc.replace("T", " ")

    params = {
        "format": "text",
        "COMMAND": "'10'",
        "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES",
        "EPHEM_TYPE": "VECTORS",
        "CENTER": "coord@301",
        "COORD_TYPE": "GEODETIC",
        "SITE_COORD": f"{longitude},{latitude},0",
        "TLIST": f"'{horizons_time}'",
        "TLIST_TYPE": "CAL",
        "TIME_TYPE": "UT",
        "REF_PLANE": "FRAME",
        "REF_SYSTEM": "ICRF",
        "VEC_CORR": "NONE",
        "VEC_TABLE": "1",
        "VEC_LABELS": "YES",
        "CSV_FORMAT": "YES",
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    content = response.text

    if "$$SOE" not in content or "$$EOE" not in content:
        raise ValueError(
            f"Horizons returned no usable ephemeris data: "
            f"{content[:500]}"
        )

    section = content.split("$$SOE", 1)[1].split(
        "$$EOE", 1
    )[0]

    rows = list(csv.reader(io.StringIO(section)))

    for row in rows:
        if len(row) < 5:
            continue

        try:
            x, y, z = map(float, row[2:5])

            if not all(math.isfinite(v) for v in (x, y, z)):
                continue

            return {
                "x": x,
                "y": y,
                "z": z,
                "raw_row": row,
                "source": "JPL Horizons",
            }

        except (ValueError, TypeError):
            continue

    raise ValueError("Could not parse Horizons position vector.")


# --------------------------------------------------
# CACHE
# --------------------------------------------------

def load_cache():

    if not CACHE_FILE.exists():
        return {}

    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache):

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    CACHE_FILE.write_text(
        json.dumps(cache, indent=4),
        encoding="utf-8",
    )


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

def validate_case(site, utc, cache):

    name, latitude, longitude = site

    cache_key = f"{name}|{utc}"

    if cache_key in cache:
        horizons = cache[cache_key]
    else:
        horizons = query_horizons(
            latitude,
            longitude,
            utc,
        )

        cache[cache_key] = horizons
        save_cache(cache)

        # Avoid sending requests too quickly.
        time.sleep(1.2)

    lunarlink = calculate_solar_geometry(
        latitude=latitude,
        longitude=longitude,
        utc=utc,
        kernel_paths=KERNELS,
        frame=FRAME,
    )

    et = lunarlink["et"]

    horizons_icrf = np.array([
        horizons["x"],
        horizons["y"],
        horizons["z"],
    ])

    # Transform Horizons ICRF vector into LunarLink's
    # Moon-centred body-fixed frame
    from calculations.spice_geometry import (
      load_kernel_set,
      unload_kernel_set,
    )

    transform_kernels = load_kernel_set(KERNELS)

    try:
        rotation = spice.pxform(
         "J2000",
         FRAME,
         et,
        )
    finally:
        unload_kernel_set(transform_kernels)

    horizons_me = rotation @ horizons_icrf

    lunarlink_vector = (
        np.array(lunarlink["sun_position_moon_centered_km"])
        - np.array(lunarlink["site_position_km"])
    )

    vector_difference = horizons_me - lunarlink_vector

    vector_error = float(np.linalg.norm(vector_difference))

    angular_error = angular_difference_deg(
        horizons_me,
        lunarlink_vector,
    )

    east, north, up = calculate_local_basis(
        latitude,
        longitude,
        lunarlink["lunar_radii_km"],
    )

    horizons_elevation, horizons_azimuth = calculate_solar_angles(
        horizons_me,
        east,
        north,
        up,
    )

    lunarlink_elevation = lunarlink["solar_elevation_deg"]
    lunarlink_azimuth = lunarlink["solar_azimuth_deg"]

    elevation_error = abs(
        horizons_elevation - lunarlink_elevation
    )

    azimuth_error = azimuth_difference(
        horizons_azimuth,
        lunarlink_azimuth,
    )

    visibility_agrees = (
        (horizons_elevation > 0)
        == (lunarlink_elevation > 0)
    )

    passed = (
        vector_error <= VECTOR_TOLERANCE_KM
        and angular_error <= ANGLE_TOLERANCE_DEG
        and elevation_error <= ANGLE_TOLERANCE_DEG
        and (
            azimuth_error is None
            or azimuth_error <= ANGLE_TOLERANCE_DEG
        )
        and visibility_agrees
    )
    return {
        "site": name,
        "latitude_deg": latitude,
        "longitude_deg": longitude,
        "utc": utc,
        "horizons_vector_icrf_km": horizons_icrf.tolist(),
        "horizons_vector_moon_me_km": horizons_me.tolist(),
        "lunarlink_vector_moon_me_km": lunarlink_vector.tolist(),
        "vector_error_km": vector_error,
        "angular_error_deg": angular_error,
        "horizons_elevation_deg": horizons_elevation,
        "lunarlink_elevation_deg": lunarlink_elevation,
        "elevation_error_deg": elevation_error,
        "horizons_azimuth_deg": horizons_azimuth,
        "lunarlink_azimuth_deg": lunarlink_azimuth,
        "azimuth_error_deg": azimuth_error,
        "geometric_visibility_agrees": visibility_agrees,
        "passed": passed,
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------


def main():

    print("\nLUNARLINK INDEPENDENT VALIDATION")
    print("=" * 65)

    cache = load_cache()
    results = []

    # Verify all required SPICE kernels exist.
    for kernel in KERNELS:
        if not kernel.is_file():
            raise FileNotFoundError(
                f"Required SPICE kernel missing: {kernel}"
            )

    # Execute all site/time combinations.
    for site in SITES:

        for utc in TIMESTAMPS:

            print(f"\nTesting {site[0]} | {utc}")

            try:
                result = validate_case(
                    site,
                    utc,
                    cache,
                )

                results.append(result)

                print(
                    f"Vector error: "
                    f"{result['vector_error_km']:.9f} km"
                )

                print(
                    f"Angular error: "
                    f"{result['angular_error_deg']:.12f} deg"
                )

                print(
                    f"Elevation error: "
                    f"{result['elevation_error_deg']:.12f} deg"
                )

                print(
                    f"Azimuth error: "
                    f"{result['azimuth_error_deg']}"
                )

                print(
                    f"RESULT: "
                    f"{'PASS' if result['passed'] else 'FAIL'}"
                )

            except Exception as exc:

                results.append({
                    "site": site[0],
                    "latitude_deg": site[1],
                    "longitude_deg": site[2],
                    "utc": utc,
                    "passed": False,
                    "error": str(exc),
                })

                print(f"ERROR: {exc}")

    # Calculate summary.
    passed = sum(
        1 for result in results
        if result.get("passed") is True
    )

    failed = len(results) - passed

    report = {
        "project": "LunarLink-DTN",
        "validation_type": "Independent solar geometry validation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_source": "NASA JPL Horizons",
        "reference_ephemeris": "DE441",
        "lunarlink_ephemeris": "DE440s",
        "reference_frame": "ICRF",
        "comparison_frame": FRAME,
        "vector_correction": "NONE",
        "sites_tested": len(SITES),
        "timestamps_tested": len(TIMESTAMPS),
        "total_cases": len(results),
        "passed": passed,
        "failed": failed,
        "vector_tolerance_km": VECTOR_TOLERANCE_KM,
        "angle_tolerance_deg": ANGLE_TOLERANCE_DEG,
        "overall_status": (
            "PASS" if failed == 0 else "FAIL"
        ),
        "results": results,
        "limitations": [
            "Uses a spherical lunar reference shape.",
            "Does not model terrain shadows.",
            "Geometric visibility is not operational communications.",
            "ICRF and SPICE J2000 alignment is assumed.",
            "Acceptance tolerances are provisional engineering values.",
        ],
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    REPORT_FILE.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8",
    )

    print("\n" + "=" * 65)
    print("VALIDATION SUMMARY")
    print("=" * 65)
    print(f"Total cases: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Overall: {report['overall_status']}")
    print(f"\nJSON report: {REPORT_FILE}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
