import importlib.util
from types import SimpleNamespace

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("server", ROOT / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def test_haversine_distance_is_reasonable():
    assert 0 < server.haversine_km(47.704, 9.828, 47.75, 9.90) < 10


def test_straight_distance_missing_coordinates_is_none():
    ad = SimpleNamespace(latitude=None, longitude=None)
    assert server.straight_distance(ad, {"latitude": 47.704, "longitude": 9.828}) is None
