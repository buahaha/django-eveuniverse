from unittest.mock import patch
from io import StringIO

from ..utils import NoSocketsTestCase

from django.core.management import call_command


PACKAGE_PATH = "eveuniverse.management.commands"


@patch(PACKAGE_PATH + ".eveuniverse_load.get_input")
@patch(PACKAGE_PATH + ".eveuniverse_load.load_map")
class TestEveAncestry(NoSocketsTestCase):
    def test_run(self, mock_load_map, mock_get_input):
        mock_get_input.return_value = "Y"

        out = StringIO()
        call_command("eveuniverse_load", stdout=out)

        self.assertTrue(mock_load_map.delay.called)
