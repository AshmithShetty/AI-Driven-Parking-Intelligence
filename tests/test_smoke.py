import unittest

from src import cis_model
from src.dashboard import route_optimizer


class SmokeTests(unittest.TestCase):
    def test_route_optimizer_returns_distance(self):
        points = [
            {"lat": 12.9716, "lon": 77.5946, "label": "A"},
            {"lat": 12.9750, "lon": 77.5990, "label": "B"},
            {"lat": 12.9650, "lon": 77.6100, "label": "C"},
        ]
        ordered, distance_km, eta_minutes = route_optimizer.optimize_waypoint_order(points)
        self.assertEqual(len(ordered), 3)
        self.assertGreaterEqual(distance_km, 0.0)
        self.assertGreaterEqual(eta_minutes, 0.0)

    def test_clip_series_bounds_values(self):
        series = cis_model.clip_series(cis_model.pd.Series([0, 10, 100]), 5, 95)
        self.assertEqual(series.tolist(), [5.0, 10.0, 95.0])


if __name__ == "__main__":
    unittest.main()
