from unittest.mock import patch
from io import StringIO

from django.test import override_settings

from ..utils import NoSocketsTestCase
from .my_test_data import EsiMockClient

from ..management.commands.eveuniverse_load import Command

from ..models import (
    EsiMapping,
    EveAncestry,
    EveAsteroidBelt,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveFaction,
    EveGraphic,
    EveGroup,
    EveMarketGroup,
    EveMoon,
    EvePlanet,
    EveRace,
    EveRegion,
    EveSolarSystem,
    EveStar,
    EveStargate,
    EveStation,
    EveType,
    EveTypeDogmaEffect,
    EveUnit,
)

PACKAGE_PATH = "eveuniverse.management.commands"


@override_settings(task_always_eager=True)
@patch(PACKAGE_PATH + ".eveuniverse_load.get_input")
@patch("eveuniverse.managers.esi")
class TestEveAncestry(NoSocketsTestCase):
    def test_minimal(self, mock_esi, mock_get_input):
        mock_esi.client = EsiMockClient()
        mock_get_input.return_value = "Y"

        # my_command = Command()
        # my_command._load_models()
