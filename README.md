# LunarLink-DTN

**Lunar South Pole Geometry and Communication Opportunity Analysis**

LunarLink-DTN is a Python-based research project exploring lunar south-pole landing-site geometry, solar visibility and future direct-to-Earth communication opportunities.

The project uses NASA/JPL SPICE ephemeris and planetary data to calculate the Sun's apparent direction relative to selected lunar surface locations.

## Current Features

- Lunar latitude and longitude validation.
- Spherical lunar coordinate conversion.
- SPICE kernel loading and ownership management.
- SPICE reference-frame recognition.
- UTC-to-ephemeris-time conversion.
- Lunar surface-site position calculations.
- Solar azimuth and elevation calculations.
- Geometric solar horizon visibility.
- Automated unit and integration tests.

## Technology Stack

- Python
- SpiceyPy
- NASA/JPL SPICE
- NumPy
- Flask
- Plotly
- Pytest

## Project Structure

```text
LunarLink-DTN/
|-- calculations/
|   |-- coordinates.py
|   |-- spice_geometry.py
|   `-- solar_geometry.py
|-- data/
|   `-- spice_kernels/
|       |-- fk/
|       |-- lsk/
|       |-- pck/
|       |-- spk/
|       `-- README.md
|-- reports/
|-- simulation/
|-- static/
|-- templates/
|-- tests/
|   |-- test_coordinates.py
|   |-- test_spice_geometry.py
|   |-- test_solar_geometry.py
|   `-- validate_solar_sites.py
|-- app.py
|-- pytest.ini
|-- requirements.txt
|-- REFERENCE_FRAMES.md
`-- README.md
```

## Scientific Data

LunarLink uses NASA/JPL SPICE kernels.

The kernel inventory and scientific configuration are documented in:

`data/spice_kernels/README.md`

Large binary kernels are excluded from Git and must be obtained separately.

## Running the Project

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run tests:

```powershell
python -m pytest -v
```

Run the solar-site validation:

```powershell
python .\tests\validate_solar_sites.py
```

## Scientific Limitations

The current solar geometry implementation:

- Uses the lunar radii supplied by the loaded planetary constants kernel.
- Calculates geometric solar elevation and azimuth.
- Does not model local terrain shadows.
- Does not calculate validated solar-panel power output.
- Does not establish operational communication availability.
- Requires independent scientific validation before mission-planning use.

Solar visibility is not equivalent to guaranteed power generation or successful communication.

## Development Roadmap

1. Validate coordinate and reference-frame conventions.
2. Independently validate solar geometry against JPL reference data.
3. Evaluate solar illumination windows across candidate landing sites.
4. Implement Earth visibility geometry.
5. Investigate communication opportunity windows.
6. Introduce terrain-aware visibility analysis.
7. Develop candidate-site comparison and visualization.
8. Integrate the scientific engine with the Flask dashboard.

## Project Principle

**Simulation before integration. Integration before operation. Verification before authorisation.**