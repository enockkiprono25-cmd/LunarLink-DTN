"""
LunarLink — SPICE Geometry Interface

Purpose:
1. Interface with NASA/JPL SPICE.
2. Validate selected kernel paths.
3. Load explicitly selected kernel files.
4. Track kernels loaded by LunarLink.
5. Protect externally loaded kernels.
6. Roll back failed loading operations.
7. Report unloading and rollback failures.

No automatic downloads are performed.
"""

from pathlib import Path
from collections.abc import Iterable
from threading import RLock
import os

import spiceypy as spice


# Tracks kernels successfully loaded by this module.
# This registry exists only for the lifetime of this Python process.
_OWNED_KERNELS = {}

# Prevents simultaneous changes to the registry.
_KERNEL_LOCK = RLock()


class KernelManagementError(RuntimeError):
    """Raised when SPICE kernel management encounters an error."""


def _path_key(path):
    """Create a normalized comparison key for a kernel path."""

    return os.path.normcase(str(path.resolve()))
def _is_meta_kernel(path):
    """
    Detect SPICE meta-kernels using their KPL/MK file signature.

    Meta-kernels are temporarily unsupported because their
    dependencies require separate ownership management.
    """

    try:
        with path.open("rb") as kernel_file:
            header = kernel_file.readline(32).strip()

        return header == b"KPL/MK"

    except OSError as error:
        raise KernelManagementError(
            f"Unable to inspect kernel file: {path}"
        ) from error

def verify_spice_engine():
    """Return information about the installed SPICE engine."""

    with _KERNEL_LOCK:

        return {
            "spiceypy_version": spice.__version__,
            "toolkit_version": spice.tkvrsn("TOOLKIT"),
            "loaded_kernels": spice.ktotal("ALL"),
            "lunarlink_owned_kernels": len(_OWNED_KERNELS),
        }

def _normalize_kernel_paths(kernel_paths, allow_empty=False):
    """Validate and normalize a collection of kernel paths."""

    if isinstance(kernel_paths, (str, bytes)):
        raise TypeError(
            "Kernel paths must be supplied as a collection."
        )

    if not isinstance(kernel_paths, Iterable):
        raise TypeError("Kernel paths must be iterable.")

    paths = list(kernel_paths)

    if not paths and not allow_empty:
        raise ValueError(
            "At least one kernel path is required."
        )

    normalized = []
    seen = set()

    for item in paths:

        if not isinstance(item, (str, Path)):
            raise TypeError(
                "Each kernel path must be a string or Path object."
            )

        path = Path(item).resolve()
        key = _path_key(path)

        if key in seen:
            raise ValueError(
                f"Duplicate kernel path detected: {path}"
            )

        seen.add(key)
        normalized.append(path)

    return normalized


def _get_loaded_kernel_keys():
    """
    Return normalized paths currently reported by SPICE.

    SpiceyPy kdata() returns four values:
    filename, file type, source and handle.
    """

    loaded = set()

    for index in range(spice.ktotal("ALL")):

        filename, _, _, _ = spice.kdata(index, "ALL")

        loaded.add(_path_key(Path(filename)))

    return loaded

def load_kernel_set(kernel_paths):
    """
    Load an explicitly supplied collection of SPICE kernels.

    Kernels already loaded by another component are not claimed
    or loaded again.

    If loading fails, previously loaded kernels from this operation
    are rolled back.

    Returns:
        List of successfully loaded kernel paths.
    """

    paths = _normalize_kernel_paths(kernel_paths)

    with _KERNEL_LOCK:

        # Validate all files before changing SPICE state.
        for path in paths:

            if not path.is_file():
                raise FileNotFoundError(
                    f"SPICE kernel not found: {path}"
                )

            if _is_meta_kernel(path):
                raise KernelManagementError(
                    f"Meta-kernels are not currently supported: {path}"
                )

        # Inspect existing SPICE state.
        loaded_before = _get_loaded_kernel_keys()

        # Reject duplicate and externally loaded kernels.
        for path in paths:

            key = _path_key(path)

            if key in _OWNED_KERNELS:
                raise KernelManagementError(
                    f"Kernel already managed by LunarLink: {path}"
                )

            if key in loaded_before:
                raise KernelManagementError(
                    f"Kernel already loaded outside this operation: {path}"
                )

        loaded = []

        try:

            for path in paths:

                before = _get_loaded_kernel_keys()

                try:
                    spice.furnsh(str(path))

                except Exception:

                    after = _get_loaded_kernel_keys()

                    newly_loaded = after - before
                    rollback_errors = []

                    for loaded_key in newly_loaded:

                        loaded_path = Path(loaded_key)

                        try:
                            spice.unload(str(loaded_path))

                        except Exception as rollback_error:

                            # Preserve ownership of kernels
                            # that could not be rolled back.
                            _OWNED_KERNELS[loaded_key] = loaded_path

                            rollback_errors.append(
                                f"{loaded_path}: {rollback_error}"
                            )

                    if rollback_errors:
                        raise KernelManagementError(
                            "SPICE loading failed and partial "
                            "rollback was unsuccessful: "
                            + "; ".join(rollback_errors)
                        )

                    raise

                # Verify successful registration.
                after = _get_loaded_kernel_keys()
                key = _path_key(path)

                if key not in after:
                    raise KernelManagementError(
                        f"SPICE did not register the loaded kernel: {path}"
                    )

                # Register ownership only after successful loading.
                loaded.append(path)
                _OWNED_KERNELS[key] = path

        except Exception as original_error:

            rollback_errors = []

            for path in reversed(loaded):

                key = _path_key(path)

                try:
                    spice.unload(str(path))

                    _OWNED_KERNELS.pop(key, None)

                except Exception as rollback_error:

                    rollback_errors.append(
                        f"{path}: {rollback_error}"
                    )

            if rollback_errors:

                raise KernelManagementError(
                    "Kernel loading failed and rollback was "
                    "incomplete. Remaining owned kernels: "
                    + "; ".join(rollback_errors)
                ) from original_error

            raise

        return loaded

def unload_kernel_set(kernel_paths):
    """
    Unload only kernels owned by LunarLink.

    Ownership is removed only after successful unloading.

    Returns:
        List of successfully unloaded kernel paths.
    """

    paths = _normalize_kernel_paths(
        kernel_paths,
        allow_empty=True
    )

    with _KERNEL_LOCK:

        # Validate ownership before unloading anything.
        for path in paths:

            key = _path_key(path)

            if key not in _OWNED_KERNELS:
                raise PermissionError(
                    f"LunarLink does not own this kernel: {path}"
                )

        unloaded = []
        errors = []

        for path in reversed(paths):

            key = _path_key(path)

            try:

                spice.unload(str(path))

                _OWNED_KERNELS.pop(key, None)
                unloaded.append(path)

            except Exception as error:

                errors.append(
                    f"{path}: {error}"
                )

        if errors:

            raise KernelManagementError(
                "Some kernels could not be unloaded. "
                "Successful unloads: "
                f"{len(unloaded)}. Failures: "
                + "; ".join(errors)
            )

        return unloaded