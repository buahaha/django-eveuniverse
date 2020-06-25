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


class EsiMockClient:
    pass

    @classmethod
    def _generate(cls):
        """dnamically generates the client class with all attributes based on definition
        """
        EsiEndpoint = namedtuple("EsiSpec", ["category", "method", "key"])
        esi_endpoints = [
            EsiEndpoint("Dogma", "get_dogma_attributes_attribute_id", "attribute_id"),
            EsiEndpoint("Dogma", "get_dogma_effects_effect_id", "effect_id"),
            EsiEndpoint(
                "Market", "get_markets_groups_market_group_id", "market_group_id"
            ),
            EsiEndpoint("Universe", "get_universe_ancestries", None),
            EsiEndpoint(
                "Universe",
                "get_universe_asteroid_belts_asteroid_belt_id",
                "asteroid_belt_id",
            ),
            EsiEndpoint("Universe", "get_universe_bloodlines", None),
            EsiEndpoint(
                "Universe", "get_universe_categories_category_id", "category_id"
            ),
            EsiEndpoint(
                "Universe",
                "get_universe_constellations_constellation_id",
                "constellation_id",
            ),
            EsiEndpoint("Universe", "get_universe_factions", None),
            EsiEndpoint("Universe", "get_universe_graphics_graphic_id", "graphic_id"),
            EsiEndpoint("Universe", "get_universe_groups_group_id", "group_id"),
            EsiEndpoint("Universe", "get_universe_moons_moon_id", "moon_id"),
            EsiEndpoint("Universe", "get_universe_moons_moon_id", "moon_id"),
            EsiEndpoint("Universe", "get_universe_planets_planet_id", "planet_id"),
            EsiEndpoint("Universe", "get_universe_races", None),
            EsiEndpoint("Universe", "get_universe_regions_region_id", "region_id"),
            EsiEndpoint(
                "Universe", "get_universe_stargates_stargate_id", "stargate_id"
            ),
            EsiEndpoint("Universe", "get_universe_stars_star_id", "star_id"),
            EsiEndpoint("Universe", "get_universe_stations_station_id", "station_id"),
            EsiEndpoint("Universe", "get_universe_systems_system_id", "system_id"),
            EsiEndpoint("Universe", "get_universe_types_type_id", "type_id"),
        ]
        for endpoint in esi_endpoints:
            if not hasattr(cls, endpoint.category):
                setattr(
                    cls, endpoint.category, type(endpoint.category, (object,), dict())
                )
            my_category = getattr(cls, endpoint.category)
            if not hasattr(my_category, endpoint.method):
                setattr(
                    my_category,
                    endpoint.method,
                    EsiRoute(endpoint.category, endpoint.method, endpoint.key).call,
                )


EsiMockClient._generate()


def _load_esi_data():
    with open(_currentdir + "/esi_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


esi_data = _load_esi_data()
