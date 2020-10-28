from collections import OrderedDict
import inspect
import json
import os
from unittest.mock import patch

from .my_test_data import EsiClientStub
from ..models import EveCategory, EveGroup, EveType, EveRegion
from ..tools.testdata import create_testdata, load_testdata_from_file, ModelSpec
from ..utils import NoSocketsTestCase

_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

FILENAME_TESTDATA = "dummy.json"


class TestTestData(NoSocketsTestCase):
    def setUp(self) -> None:
        EveCategory.objects.all().delete
        EveGroup.objects.all().delete
        EveType.objects.all().delete
        EveRegion.objects.all().delete

    @staticmethod
    def _get_ids(testdata: dict, model_name: str) -> set:
        return {x["id"] for x in testdata[model_name]}

    @patch("eveuniverse.models.EVEUNIVERSE_LOAD_STARGATES", True)
    @patch("eveuniverse.tools.testdata.is_esi_online", lambda: True)
    @patch("eveuniverse.managers.esi")
    def test_create_testdata(self, mock_esi):
        mock_esi.client = EsiClientStub()

        spec = [
            ModelSpec("EveType", ids=[603]),
            ModelSpec("EveType", ids=[621]),
            ModelSpec("EveSolarSystem", ids=[30045339], include_children=True),
        ]
        filepath = f"{_currentdir}/{FILENAME_TESTDATA}"
        create_testdata(spec, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            testdata = json.load(f, object_pairs_hook=OrderedDict)

        # EveType
        # did load requested objects
        self.assertEqual(self._get_ids(testdata, "EveType"), {16, 603, 621})

        # did load their partents too
        self.assertEqual(self._get_ids(testdata, "EveCategory"), {2, 6})
        self.assertEqual(self._get_ids(testdata, "EveGroup"), {10, 25, 26})

        # did not load their children
        self.assertEqual(EveType.objects.get(id=603).dogma_attributes.count(), 0)

        # EveSolarSystem
        # did load requested objects
        self.assertEqual(self._get_ids(testdata, "EveSolarSystem"), {30045339})

        # did load their partents too
        self.assertEqual(self._get_ids(testdata, "EveConstellation"), {20000785})

        # did load children of solar systems as requested
        self.assertEqual(self._get_ids(testdata, "EveStargate"), {50016284, 50016286})

        os.remove(filepath)

    def test_load_testdata_from_file(self):
        filepath = f"{_currentdir}/testdata_example.json"
        load_testdata_from_file(filepath)
        self.assertTrue(EveCategory.objects.filter(id=6).exists())
        self.assertTrue(EveGroup.objects.filter(id=25).exists())
        self.assertTrue(EveGroup.objects.filter(id=26).exists())
        self.assertTrue(EveType.objects.filter(id=603).exists())
        self.assertTrue(EveType.objects.filter(id=621).exists())
        self.assertTrue(EveRegion.objects.filter(id=10000069).exists())
