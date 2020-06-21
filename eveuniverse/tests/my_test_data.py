import inspect
import json
import os
from unittest.mock import Mock


_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


"""ESI mock client"""


class EsiRoute:
    def __init__(self, category, method, primary_key):
        self._category = category
        self._method = method
        self._primary_key = primary_key

    def call(self, **kwargs):
        try:
            pk_value = str(kwargs[self._primary_key])
            result = esi_data[self._category][self._method][pk_value]
        except KeyError:
            raise KeyError(
                "No test data for %s.%s with %s = %s"
                % (self._category, self._method, self._primary_key, pk_value)
            ) from None
        return Mock(**{"results.return_value": result, "result.return_value": result})


def esi_mock_client():
    mock_client = Mock()

    # Dogma
    mock_client.Dogma.get_dogma_attributes_attribute_id.side_effect = EsiRoute(
        "Dogma", "get_dogma_attributes_attribute_id", "attribute_id"
    ).call
    mock_client.Dogma.get_dogma_effects_effect_id.side_effect = EsiRoute(
        "Dogma", "get_dogma_effects_effect_id", "effect_id"
    ).call

    # Market
    mock_client.Market.get_markets_groups_market_group_id.side_effect = EsiRoute(
        "Market", "get_markets_groups_market_group_id", "market_group_id"
    ).call

    # Universe
    mock_client.Universe.get_universe_categories_category_id.side_effect = EsiRoute(
        "Universe", "get_universe_categories_category_id", "category_id"
    ).call

    mock_client.Universe.get_universe_groups_group_id.side_effect = EsiRoute(
        "Universe", "get_universe_groups_group_id", "group_id"
    ).call

    mock_client.Universe.get_universe_types_type_id.side_effect = EsiRoute(
        "Universe", "get_universe_types_type_id", "type_id"
    ).call

    return mock_client


def _load_esi_data():
    with open(_currentdir + "/esi_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


esi_data = _load_esi_data()
