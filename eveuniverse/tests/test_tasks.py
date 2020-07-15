from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings

from .my_test_data import EsiClientStub
from ..models import EveRegion, EveConstellation, EveSolarSystem
from ..tasks import load_eve_object, load_map, update_or_create_eve_object
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

    @patch("eveuniverse.managers.esi")
    def test_update_or_create_eve_object(self, mock_esi):
        mock_esi.client = EsiClientStub()
        obj, _ = EveRegion.objects.update_or_create_esi(id=10000002)
        obj.name = "Dummy"
        obj.save()

        update_or_create_eve_object(
            "EveRegion", 10000002, include_children=False, wait_for_children=False
        )

        obj.refresh_from_db()
        self.assertNotEqual(obj.name, "Dummy")


class TestLoadMap(TestCase):
    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch(MODULE_PATH + ".esi")
    @patch("eveuniverse.managers.esi")
    def test_load_map(self, mock_esi_1, mock_esi_2):
        mock_esi_1.client = EsiClientStub()
        mock_esi_2.client = EsiClientStub()
        load_map()

        for id in [10000002, 10000014, 10000069, 11000031]:
            self.assertTrue(EveRegion.objects.filter(id=id).exists())

        for id in [20000169, 20000785, 21000324]:
            self.assertTrue(EveConstellation.objects.filter(id=id).exists())

        for id in [30001161, 30045339, 31000005]:
            self.assertTrue(EveSolarSystem.objects.filter(id=id).exists())
