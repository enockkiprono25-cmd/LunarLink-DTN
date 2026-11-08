from pathlib import Path

import pytest

from calculations.solar_geometry import calculate_solar_geometry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KERNEL_DIR = PROJECT_ROOT / "data" / "spice_kernels"

KERNELS = [
    KERNEL_DIR / "lsk" / "naif0012.tls",
    KERNEL_DIR / "spk" / "de440s.bsp",
    KERNEL_DIR / "pck" / "moon_pa_de440_200625.bpc",
    KERNEL_DIR / "pck" / "pck00011.tpc",
    KERNEL_DIR / "fk" / "moon_de440_250416.tf",
]


@pytest.mark.integration
def test_solar_geometry_calculation():

    result = calculate_solar_geometry(
        latitude=-89.0,
        longitude=0.0,
        utc="2026-11-08T12:00:00",
        kernel_paths=KERNELS,
        frame="MOON_ME",
    )

    assert result["frame"] == "MOON_ME"
    assert result["sun_distance_site_km"] > 0
    assert -90 <= result["solar_elevation_deg"] <= 90

    if result["solar_azimuth_deg"] is not None:
        assert 0 <= result["solar_azimuth_deg"] < 360

    assert isinstance(
        result["geometric_horizon_visible"],
        bool,
    )

    print("\nSolar geometry result:")
    for key, value in result.items():
        print(f"{key}: {value}")