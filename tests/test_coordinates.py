import math
import unittest

from calculations.coordinates import (
    validate_lunar_coordinates,
    lunar_lat_lon_to_unit_vector,
)


class TestLunarCoordinates(unittest.TestCase):

    def test_valid_coordinates(self):
        self.assertTrue(
            validate_lunar_coordinates(0, 0)
        )

    def test_invalid_latitude(self):
        with self.assertRaises(ValueError):
            validate_lunar_coordinates(91, 0)

    def test_invalid_longitude(self):
        with self.assertRaises(ValueError):
            validate_lunar_coordinates(0, 181)

    def test_boolean_coordinates_rejected(self):
        with self.assertRaises(TypeError):
            validate_lunar_coordinates(True, 0)

    def test_non_finite_coordinates_rejected(self):

        for value in (float("nan"), float("inf"), float("-inf")):

            with self.subTest(value=value):

                with self.assertRaises(ValueError):
                    validate_lunar_coordinates(value, 0)

    def test_south_pole_vector(self):
        result = lunar_lat_lon_to_unit_vector(-90, 0)

        self.assertEqual(result["x"], 0.0)
        self.assertEqual(result["y"], 0.0)
        self.assertAlmostEqual(result["z"], -1.0)

    def test_north_pole_vector(self):
        result = lunar_lat_lon_to_unit_vector(90, 0)

        self.assertEqual(result["x"], 0.0)
        self.assertEqual(result["y"], 0.0)
        self.assertAlmostEqual(result["z"], 1.0)

    def test_equator_zero_longitude(self):
        result = lunar_lat_lon_to_unit_vector(0, 0)

        self.assertAlmostEqual(result["x"], 1.0)
        self.assertAlmostEqual(result["y"], 0.0)
        self.assertAlmostEqual(result["z"], 0.0)

    def test_equator_ninety_east(self):
        result = lunar_lat_lon_to_unit_vector(0, 90)

        self.assertAlmostEqual(result["x"], 0.0, places=10)
        self.assertAlmostEqual(result["y"], 1.0, places=10)
        self.assertAlmostEqual(result["z"], 0.0)

    def test_vector_has_unit_length(self):
        result = lunar_lat_lon_to_unit_vector(45, 60)

        magnitude = math.sqrt(
            result["x"] ** 2
            + result["y"] ** 2
            + result["z"] ** 2
        )

        self.assertAlmostEqual(magnitude, 1.0, places=10)


if __name__ == "__main__":
    unittest.main()