# LunarLink — Reference Frames and Scientific Conventions

## 1. Purpose

This document defines the coordinate conventions, reference-frame considerations, measurement units and scientific validation policies used by LunarLink.

Its purpose is to ensure that calculations involving lunar locations, solar visibility, Earth visibility and communication windows use consistent and traceable scientific inputs.

The conventions documented here are development policies. They must be verified against the actual scientific datasets and SPICE kernels before being treated as operational configurations.

## 2. Lunar Reference Frames

LunarLink will evaluate the following candidate reference frames:

**MOON_ME**

Mean Earth/rotation-axis lunar reference frame.

**MOON_PA**

Principal Axes lunar reference frame.

**J2000**

Inertial reference frame used for representing celestial positions and vectors.

**IAU_MOON**

A lunar body-fixed reference frame that will also be evaluated for compatibility with the selected SPICE data.

### Frame Selection Policy

These are candidate frames, not yet verified operational configurations.

The final lunar reference frame will be selected after inspecting the actual SPICE kernel definitions, coverage and compatibility.

All transformations must use compatible reference-frame definitions and kernels.

Frame selection must consider the scientific purpose, kernel solution, coverage period and availability of required transformations.

## 3. Lunar Coordinate Conventions

LunarLink will use the following intended coordinate conventions for its initial coordinate utilities:

* Latitude: planetocentric latitude.
* Longitude: east-positive longitude.
* Latitude unit: degrees at the user-input boundary.
* Longitude unit: degrees at the user-input boundary.
* Longitude input range: -180° to +180°.
* Latitude input range: -90° to +90°.

The final interpretation of latitude and longitude must be checked against the source dataset.

A coordinate pair must not be assumed to use these conventions merely because its values fall within the expected numerical ranges.

## 4. Internal Measurement Units

LunarLink will maintain explicit unit conventions.

| Quantity                      | Intended unit          |
| ----------------------------- | ---------------------- |
| User-entered latitude         | Degrees                |
| User-entered longitude        | Degrees                |
| Internal angular calculations | Radians                |
| Distance                      | Kilometres             |
| Solar elevation               | Degrees for display    |
| Time input                    | UTC                    |
| SPICE ephemeris time          | ET                     |
| Illumination                  | Fraction or percentage |

Conversions between units must be explicit.

Calculations must not silently mix degrees and radians, or kilometres and other distance units.

## 5. Time Standards

User-facing dates and times will use UTC unless a specific interface requirement establishes another display convention.

SPICE calculations use ephemeris time.

Time conversion must be performed using an appropriate SPICE time kernel, including a leap-seconds kernel where required.

The selected kernel and time conversion assumptions must be recorded.

## 6. Scientific Data Sources

The intended scientific data sources include:

**NASA/JPL SPICE**

Primary framework for ephemeris data, reference frames, time conversion and geometric calculations.

**JPL Horizons**

An independent source for checking selected astronomical positions and time-dependent results.

The exact datasets, kernels and versions used must be documented.

The presence of a software library does not establish that the required scientific data have been downloaded or validated.

## 7. SPICE Kernel Management

LunarLink will load only explicitly selected kernel files.

Kernel management must:

1. Validate kernel paths before loading.
2. Reject missing files.
3. Avoid silently downloading external data.
4. Record the kernels loaded for a calculation.
5. Handle loading failures.
6. Support controlled unloading of kernels.

Kernel compatibility must be checked before geometry calculations.

The kernel inventory should record:

* Kernel filename.
* Kernel type.
* Source.
* Version or solution identifier where available.
* Coverage period.
* Reference-frame definitions.
* Relevant limitations.

## 8. Data Provenance

Every scientific calculation should be traceable to its inputs.

Where applicable, LunarLink should record:

* Original data source.
* Dataset or kernel filename.
* Dataset version.
* Retrieval date.
* Time coverage.
* Coordinate system.
* Reference frame.
* Measurement units.
* Applied transformations.
* Software and library versions.

Original scientific source files must remain unchanged.

Derived datasets should be stored separately from their original inputs.

## 9. Scientific Validation

LunarLink must validate its calculations before presenting them as scientifically reliable.

Validation should include:

* Coordinate range checks.
* Finite numerical values.
* Timestamp validation.
* Unit consistency.
* Reference-frame compatibility.
* Kernel coverage checks.
* Missing-data detection.
* Independent comparison against authoritative references where possible.

A passing software test confirms expected software behaviour for the tested case. It does not independently prove scientific accuracy.

## 10. Solar Visibility

Solar visibility calculations will evaluate the position of the Sun relative to a selected lunar location and local horizon.

The calculation must account for:

* Lunar location.
* Reference frame.
* Observation time.
* Solar position.
* Local surface orientation.
* Relevant geometric assumptions.

Solar elevation and illumination must be distinguished.

A positive solar elevation may indicate geometric visibility under the selected horizon model, but it does not by itself establish actual surface illumination under every terrain condition.

Terrain obstruction and local topography may require additional datasets and modelling.

## 11. Earth Visibility and Communication Geometry

Earth visibility calculations will evaluate whether Earth is geometrically visible from a selected lunar location.

The calculation must identify:

* Observation location.
* Observation time.
* Earth position.
* Lunar reference frame.
* Local horizon.
* Geometric assumptions.

Geometric visibility is not equivalent to an operational communication link.

Actual communications also depend on antenna orientation, hardware, link budget, signal conditions and mission infrastructure.

## 12. Known Implementation Limitations

The current coordinate utility performs basic spherical coordinate conversion into a Moon-centred unit vector.

It does not yet implement a complete lunar body-fixed position model.

The current SPICE interface supports kernel management but does not yet establish validated lunar geometry calculations.

No actual lunar reference-frame solution or operational kernel combination has been approved.

Terrain modelling, solar illumination validation and Earth visibility validation remain future development tasks.

## 13. Development and Verification Policy

LunarLink follows these principles:

* Preserve original scientific data.
* Record data provenance.
* Use explicit coordinate and unit conventions.
* Keep calculations modular.
* Test individual components.
* Validate scientific outputs independently.
* Document assumptions and limitations.
* Distinguish simulation from real mission operations.

**Development principle:**

Simulation before integration.

Integration before operation.

Verification before authorisation.
