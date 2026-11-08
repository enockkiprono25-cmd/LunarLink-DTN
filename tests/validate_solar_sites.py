from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from calculations.solar_geometry import calculate_solar_geometry

ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = ROOT / "data" / "spice_kernels"

KERNELS = [
    KERNEL_DIR / "lsk" / "naif0012.tls",
    KERNEL_DIR / "spk" / "de440s.bsp",
    KERNEL_DIR / "pck" / "moon_pa_de440_200625.bpc",
    KERNEL_DIR / "pck" / "pck00011.tpc",
    KERNEL_DIR / "fk" / "moon_de440_250416.tf",
]

UTC = "2026-11-08T12:00:00"

SITES = [
    ("South Pole", -90.0, 0.0),
    ("Near South Pole", -89.0, 0.0),
    ("High Latitude East", -85.0, 90.0),
    ("Equatorial Reference", 0.0, 0.0),
]

print("\nLUNARLINK SOLAR GEOMETRY VALIDATION")
print("=" * 65)

for name, latitude, longitude in SITES:

    result = calculate_solar_geometry(
        latitude=latitude,
        longitude=longitude,
        utc=UTC,
        kernel_paths=KERNELS,
        frame="MOON_ME",
    )

    print(f"\nSite: {name}")
    print(f"Coordinates: {latitude}°, {longitude}°")
    print(
        f"Solar elevation: "
        f"{result['solar_elevation_deg']:.6f}°"
    )
    print(
        f"Solar azimuth: "
        f"{result['solar_azimuth_deg']}"
    )
    print(
        f"Geometric visibility: "
        f"{result['geometric_horizon_visible']}"
    )
    print(
        f"Sun distance: "
        f"{result['sun_distance_site_km']:.3f} km"
    )

print("\nValidation run completed.")