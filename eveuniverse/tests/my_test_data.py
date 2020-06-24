from collections import namedtuple
import inspect
import json
import os
from unittest.mock import Mock


_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


"""ESI mock client"""


class EsiRoute:
    def __init__(self, category, method, primary_key=None):
        self._category = category
        self._method = method
        self._primary_key = primary_key

    def call(self, **kwargs):
        try:
            pk_value = None
            if self._primary_key:
                if self._primary_key not in kwargs:
                    raise ValueError(
                        f"{self._category}.{self._method}: Missing primary key: "
                        f"{self._primary_key}"
                    )
                pk_value = str(kwargs[self._primary_key])
                result = esi_data[self._category][self._method][pk_value]
            else:
                result = esi_data[self._category][self._method]
        except KeyError:
            raise KeyError(
                f"{self._category}.{self._method}: No test data for "
                f"{self._primary_key} = {pk_value}"
            ) from None
        return Mock(**{"results.return_value": result, "result.return_value": result})


def _generate_esi_client_mock():
    EsiEndpoint = namedtuple("EsiSpec", ["category", "method", "key"])
    esi_endpoints = [
        EsiEndpoint("Dogma", "get_dogma_attributes_attribute_id", "attribute_id"),
        EsiEndpoint("Dogma", "get_dogma_effects_effect_id", "effect_id"),
        EsiEndpoint("Market", "get_markets_groups_market_group_id", "market_group_id"),
        EsiEndpoint("Universe", "get_universe_ancestries", None),
        EsiEndpoint(
            "Universe",
            "get_universe_asteroid_belts_asteroid_belt_id",
            "asteroid_belt_id",
        ),
        EsiEndpoint("Universe", "get_universe_bloodlines", None),
        EsiEndpoint("Universe", "get_universe_categories_category_id", "category_id"),
        EsiEndpoint(
            "Universe",
            "get_universe_constellations_constellation_id",
            "constellation_id",
        ),
        EsiEndpoint("Universe", "get_universe_groups_group_id", "group_id"),
        EsiEndpoint("Universe", "get_universe_moons_moon_id", "moon_id"),
        EsiEndpoint("Universe", "get_universe_moons_moon_id", "moon_id"),
        EsiEndpoint("Universe", "get_universe_planets_planet_id", "planet_id"),
        EsiEndpoint("Universe", "get_universe_races", None),
        EsiEndpoint("Universe", "get_universe_regions_region_id", "region_id"),
        EsiEndpoint("Universe", "get_universe_stars_star_id", "star_id"),
        EsiEndpoint("Universe", "get_universe_stations_station_id", "station_id"),
        EsiEndpoint("Universe", "get_universe_systems_system_id", "system_id"),
        EsiEndpoint("Universe", "get_universe_types_type_id", "type_id"),
    ]

    args = dict()
    for endpoint in esi_endpoints:
        args[f"{endpoint.category}.{endpoint.method}.side_effect"] = EsiRoute(
            endpoint.category, endpoint.method, endpoint.key
        ).call
    mock_client = Mock(name="esi_mock_client", **args)

    return mock_client


esi_mock_client = _generate_esi_client_mock()


def _load_esi_data():
    with open(_currentdir + "/esi_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


esi_data = _load_esi_data()
