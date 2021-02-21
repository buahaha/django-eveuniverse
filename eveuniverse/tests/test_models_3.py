from unittest.mock import patch

import requests_mock

from .testdata.esi import EsiClientStub
from .testdata.sde import sde_data
from ..models import EveType, EveTypeMaterial
from ..utils import NoSocketsTestCase


MODELS_PATH = "eveuniverse.models"
MANAGERS_PATH = "eveuniverse.managers"


@patch(MANAGERS_PATH + ".esi")
class TestEveTypeMaterial(NoSocketsTestCase):
    @staticmethod
    def _render_cache_content():
        type_material_data_all = dict()
        for row in sde_data["type_materials"]:
            type_id = row["typeID"]
            if type_id not in type_material_data_all:
                type_material_data_all[type_id] = list()
            type_material_data_all[type_id].append(row)
        return type_material_data_all

    @patch(MANAGERS_PATH + ".cache")
    @requests_mock.Mocker()
    def test_should_create_new_instance(self, mock_cache, mock_esi, requests_mocker):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)
        # when
        EveTypeMaterial.objects.update_or_create_api(eve_type=eve_type)
        # then
        self.assertTrue(requests_mocker.called)
        self.assertTrue(mock_cache.set.called)
        self.assertSetEqual(
            set(
                EveTypeMaterial.objects.filter(eve_type_id=603).values_list(
                    "material_eve_type_id", flat=True
                )
            ),
            {34, 35, 36, 37, 38, 39, 40},
        )
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=34)
        self.assertEqual(obj.quantity, 21111)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=35)
        self.assertEqual(obj.quantity, 8889)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=36)
        self.assertEqual(obj.quantity, 3111)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=37)
        self.assertEqual(obj.quantity, 589)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=38)
        self.assertEqual(obj.quantity, 2)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=39)
        self.assertEqual(obj.quantity, 4)
        obj = EveTypeMaterial.objects.get(eve_type_id=603, material_eve_type_id=40)
        self.assertEqual(obj.quantity, 4)

    @patch(MANAGERS_PATH + ".cache")
    @requests_mock.Mocker()
    def test_should_use_cache_if_available(self, mock_cache, mock_esi, requests_mocker):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = self._render_cache_content()
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        eve_type, _ = EveType.objects.get_or_create_esi(id=603)
        # when
        EveTypeMaterial.objects.update_or_create_api(eve_type=eve_type)
        # then
        self.assertFalse(requests_mocker.called)
        self.assertFalse(mock_cache.set.called)
        self.assertSetEqual(
            set(
                EveTypeMaterial.objects.filter(eve_type_id=603).values_list(
                    "material_eve_type_id", flat=True
                )
            ),
            {34, 35, 36, 37, 38, 39, 40},
        )
