from unittest.mock import patch
from io import StringIO

from ..utils import NoSocketsTestCase

from django.core.management import call_command


PACKAGE_PATH = "eveuniverse.management.commands"


@patch(PACKAGE_PATH + ".eveuniverse_load_data.get_input")
class TestLoadCommand(NoSocketsTestCase):
    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_map")
    def test_load_data_map(self, mock_load_map, mock_get_input):
        mock_get_input.return_value = "Y"

        out = StringIO()
        call_command("eveuniverse_load_data", "map", stdout=out)

        self.assertTrue(mock_load_map.delay.called)

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_ship_types")
    def test_load_data_ship_types(self, mock_load_ship_types, mock_get_input):
        mock_get_input.return_value = "Y"

        out = StringIO()
        call_command("eveuniverse_load_data", "ships", stdout=out)

        self.assertTrue(mock_load_ship_types.delay.called)

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_structure_types")
    def test_load_data_structure_types(self, mock_load_structure_types, mock_get_input):
        mock_get_input.return_value = "Y"

        out = StringIO()
        call_command("eveuniverse_load_data", "structures", stdout=out)

        self.assertTrue(mock_load_structure_types.delay.called)
