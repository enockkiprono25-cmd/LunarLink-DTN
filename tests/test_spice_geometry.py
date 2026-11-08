import unittest
import tempfile

from pathlib import Path
from unittest.mock import patch

import spiceypy as spice

from calculations.spice_geometry import (
    verify_spice_engine,
    load_kernel_set,
    unload_kernel_set,
    KernelManagementError,
)

class TestSpiceGeometry(unittest.TestCase):
    def test_empty_unload_returns_empty_list(self):
        result = unload_kernel_set([])

        self.assertEqual(result, [])


    def test_unowned_kernel_cannot_be_unloaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "external.tpc"
            kernel.write_text("temporary test file")

            with self.assertRaises(PermissionError):
                unload_kernel_set([kernel])

    def test_duplicate_loading_by_lunarlink_is_rejected(self):
        kernel_content = (
            "KPL/PCK\n"
            "\\begindata\n"
            "BODY399_RADII = "
            "( 6378.140, 6378.140, 6356.755 )\n"
            "\\begintext\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "duplicate.tpc"
            kernel.write_text(kernel_content, encoding="ascii")

            try:
                load_kernel_set([kernel])

                with self.assertRaises(KernelManagementError):
                    load_kernel_set([kernel])

            finally:
                unload_kernel_set([kernel])


    def test_externally_loaded_kernel_is_not_claimed(self):
        kernel_content = (
            "KPL/PCK\n"
            "\\begindata\n"
            "BODY399_RADII = "
            "( 6378.140, 6378.140, 6356.755 )\n"
            "\\begintext\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "external.tpc"
            kernel.write_text(kernel_content, encoding="ascii")

            try:
                spice.furnsh(str(kernel.resolve()))

                with self.assertRaises(KernelManagementError):
                    load_kernel_set([kernel])

            finally:
                spice.unload(str(kernel.resolve()))


    def test_failed_unload_preserves_ownership(self):
        kernel_content = (
            "KPL/PCK\n"
            "\\begindata\n"
            "BODY399_RADII = "
            "( 6378.140, 6378.140, 6356.755 )\n"
            "\\begintext\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "unload_failure.tpc"
            kernel.write_text(kernel_content, encoding="ascii")

            try:
                load_kernel_set([kernel])

                with patch(
                    "calculations.spice_geometry.spice.unload",
                    side_effect=RuntimeError("Simulated unload failure")
                ):
                    with self.assertRaises(KernelManagementError):
                        unload_kernel_set([kernel])

                # Ownership should still exist after failed unloading.
                self.assertEqual(
                    verify_spice_engine()["lunarlink_owned_kernels"],
                    1
                )

            finally:
                unload_kernel_set([kernel])
    def test_spice_engine_information(self):
        result = verify_spice_engine()

        self.assertEqual(
            result["spiceypy_version"],
            spice.__version__
        )

        self.assertTrue(
            result["toolkit_version"].startswith("CSPICE")
        )

        self.assertIsInstance(
            result["loaded_kernels"],
            int
        )

    def test_empty_kernel_list_rejected(self):
        with self.assertRaises(ValueError):
            load_kernel_set([])

    def test_missing_kernel_rejected(self):
        with self.assertRaises(FileNotFoundError):
            load_kernel_set([
                "data/spice_kernels/nonexistent_kernel.tpc"
            ])

    def test_invalid_input_type_rejected(self):
        with self.assertRaises(TypeError):
            load_kernel_set("kernel.tpc")

    def test_duplicate_kernel_paths_rejected(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "test.tpc"
            kernel.write_text("temporary test file")

            with self.assertRaises(ValueError):
                load_kernel_set([kernel, kernel])

    def test_valid_kernel_loading_and_unloading(self):

        kernel_content = (
            "KPL/PCK\n"
            "\\begindata\n"
            "BODY399_RADII = "
            "( 6378.140, 6378.140, 6356.755 )\n"
            "\\begintext\n"
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            kernel = Path(temp_dir) / "test_kernel.tpc"

            kernel.write_text(
                kernel_content,
                encoding="ascii"
            )

            initial_count = spice.ktotal("ALL")

            loaded = load_kernel_set([kernel])

            self.assertEqual(len(loaded), 1)

            self.assertEqual(
                spice.ktotal("ALL"),
                initial_count + 1
            )

            unloaded = unload_kernel_set(loaded)

            self.assertEqual(len(unloaded), 1)

            self.assertEqual(
                spice.ktotal("ALL"),
                initial_count
            )

    def test_loading_failure_rolls_back_previous_kernels(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            first = Path(temp_dir) / "first.tpc"
            second = Path(temp_dir) / "second.tpc"

            first.write_text("temporary file")
            second.write_text("temporary file")

            first_key = str(first.resolve()).lower()

            # Simulate SPICE kernel-pool state.
            simulated_states = [
                set(),          # Initial state
                set(),          # Before first loading
                {first_key},    # First kernel successfully loaded
                {first_key},    # Before second loading
                {first_key},    # Second loading fails
            ]

            with patch(
                "calculations.spice_geometry._get_loaded_kernel_keys",
                side_effect=simulated_states
            ):

                with patch(
                    "calculations.spice_geometry.spice.furnsh"
                ) as mock_furnsh:

                    with patch(
                        "calculations.spice_geometry.spice.unload"
                    ) as mock_unload:

                        mock_furnsh.side_effect = [
                            None,
                            RuntimeError("Simulated loading failure")
                        ]

                        with self.assertRaises(RuntimeError):

                            load_kernel_set([first, second])

                        # First kernel must be rolled back.
                        mock_unload.assert_called_once_with(
                            str(first.resolve())
                        )

                        # No kernels should remain owned by LunarLink.
                        self.assertEqual(
                            verify_spice_engine()["lunarlink_owned_kernels"],
                            0
                        )  

if __name__ == "__main__":
    unittest.main()