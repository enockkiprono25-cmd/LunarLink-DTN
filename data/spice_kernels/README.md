# LunarLink SPICE Kernel Inventory

## Purpose

This directory stores scientific SPICE kernels
used by LunarLink's lunar geometry engine.

## Kernel Categories

- lsk: Leap-seconds kernels.
- spk: Planetary and satellite ephemerides.
- pck: Planetary constants and orientation.
- fk: Reference-frame definitions.

## Proposed Scientific Configuration

| Kernel | Type | Purpose |
|---|---|---|
| naif0012.tls | LSK | UTC to ET |
| de440s.bsp | SPK | Planetary ephemerides |
| moon_pa_de440_200625.bpc | Binary PCK | Lunar orientation |
| moon_de440_250416.tf | FK | Lunar frames |
| pck00011.tpc | Text PCK | Planetary constants |

## Validation Policy

Every kernel must be checked for:

- File integrity.
- Kernel type.
- Coverage period.
- Reference-frame compatibility.
- Scientific provenance.

No kernel configuration is considered
operational until validation succeeds.