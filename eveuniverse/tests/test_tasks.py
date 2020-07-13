from unittest.mock import patch

from .my_test_data import EsiClientStub
from ..models import EveRegion
from ..tasks import load_eve_object, load_map
from ..utils import NoSocketsTestCase, set_test_logger

MODULE_PATH = "eveuniverse.tasks"
logger = set_test_logger(MODULE_PATH, __file__)


class TestTasks(NoSocketsTestCase):
    @patch("eveuniverse.managers.esi")
    def test_load_eve_object(self, mock_esi):
        mock_esi.client = EsiClientStub()

        load_eve_object(
            "EveRegion", 10000002, include_children=False, wait_for_children=False
        )

        self.assertTrue(EveRegion.objects.filter(id=10000002).exists())

    @patch(MODULE_PATH + ".esi")
    @patch(MODULE_PATH + ".load_eve_object")
    def test_load_map(self, mock_load_eve_object, mock_esi):
        mock_esi.client = EsiClientStub()
        load_map()

        self.assertEqual(mock_load_eve_object.delay.call_count, 4)
