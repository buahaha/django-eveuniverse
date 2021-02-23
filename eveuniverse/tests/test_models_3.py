from unittest.mock import patch

import requests_mock

from .testdata.esi import EsiClientStub
from .testdata.sde import sde_data, type_materials_cache_content
from ..models import EveType, EveTypeMaterial
from ..utils import NoSocketsTestCase


MODELS_PATH = "eveuniverse.models"
MANAGERS_PATH = "eveuniverse.managers"


@patch(MANAGERS_PATH + ".cache")
@patch(MANAGERS_PATH + ".esi")
@requests_mock.Mocker()
class TestEveTypeMaterial(NoSocketsTestCase):
    def test_should_create_new_instance(self, mock_esi, mock_cache, requests_mocker):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        with patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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

    def test_should_use_cache_if_available(self, mock_esi, mock_cache, requests_mocker):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        with patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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

    def test_should_handle_no_type_materials_for_type(
        self, mock_esi, mock_cache, requests_mocker
    ):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        with patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
            eve_type, _ = EveType.objects.get_or_create_esi(id=34)
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
            set(),
        )

    def test_should_fetch_typematerials_when_creating_type_and_enabled(
        self, mock_esi, mock_cache, requests_mocker
    ):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        # when
        with patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", True):
            eve_type, _ = EveType.objects.update_or_create_esi(id=603)
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

    def test_should_ignore_typematerials_when_creating_type_and_disabled(
        self, mock_esi, mock_cache, requests_mocker
    ):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        requests_mocker.register_uri(
            "GET",
            url="https://sde.zzeve.com/invTypeMaterials.json",
            json=sde_data["type_materials"],
        )
        # when
        with patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
            eve_type, _ = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertFalse(requests_mocker.called)
        self.assertFalse(mock_cache.set.called)
        self.assertSetEqual(
            set(
                EveTypeMaterial.objects.filter(eve_type_id=603).values_list(
                    "material_eve_type_id", flat=True
                )
            ),
            set(),
        )


@patch(MANAGERS_PATH + ".cache")
@patch(MANAGERS_PATH + ".esi")
class TestEveTypeSections(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_no_enabled_sections(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, created = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.materials.count(), 0)
        self.assertFalse(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_type_materials_on_demand(
        self, mock_esi, mock_cache
    ):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        # when
        obj, created = EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.Section.TYPE_MATERIALS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.materials.count(), 7)
        self.assertTrue(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", True)
    def test_should_create_type_with_type_materials_global(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        # when
        obj, created = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.materials.count(), 7)
        self.assertTrue(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_not_fetch_type_again(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        EveType.objects.update_or_create_esi(id=603)
        # when
        obj, created = EveType.objects.get_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertFalse(created)
        self.assertEqual(obj.materials.count(), 0)
        self.assertFalse(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MANAGERS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_fetch_type_again_with_section(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        EveType.objects.update_or_create_esi(id=603)
        # when
        obj, created = EveType.objects.get_or_create_esi(
            id=603, enabled_sections=[EveType.Section.TYPE_MATERIALS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertFalse(created)
        self.assertEqual(obj.materials.count(), 7)
        self.assertTrue(obj.enabled_sections.type_materials)
