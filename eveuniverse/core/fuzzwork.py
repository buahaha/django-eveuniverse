"""Wrapper to access fuzzwork API"""
from collections import namedtuple
from typing import Optional
from urllib.parse import urlencode

import requests

from django.core.cache import cache

_CACHE_TIMEOUT = 3_600 * 12

EveItem = namedtuple("EveItem", ["id", "name", "type_id", "distance"])


def nearest_celestial(
    x: int, y: int, z: int, solar_system_id: int
) -> Optional[EveItem]:
    """Fetch nearest celestial to given coordinates from API and return it

    Results are cached. Returns None if nothing found nearby.
    """
    cache_key_base = "EVEUNIVERSE_NEAREST_CELESTIAL"
    query = urlencode(
        {
            "x": int(x),
            "y": int(y),
            "z": int(z),
            "solarsystemid": int(solar_system_id),
        }
    )
    cache_key = f"{cache_key_base}_{query}"
    data = cache.get(key=cache_key)
    if not data:
        r = requests.get(f"https://www.fuzzwork.co.uk/api/nearestCelestial.php?{query}")
        r.raise_for_status()
        data = r.json()
    if not data["itemName"]:
        return None
    cache.set(key=cache_key, value=data, timeout=_CACHE_TIMEOUT)
    result = EveItem(
        id=int(data["itemid"]),
        name=str(data["itemName"]),
        type_id=int(data["typeid"]),
        distance=float(data["distance"]),
    )
    return result
