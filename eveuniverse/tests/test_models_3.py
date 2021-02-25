from unittest.mock import patch

import requests_mock

from .testdata.esi import EsiClientStub
from .testdata.sde import sde_data, type_materials_cache_content
from ..models import EvePlanet, EveType, EveTypeMaterial, EveSolarSystem
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
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", True):
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
        with patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False):
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
class TestEveTypeWithSections(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_no_enabled_sections(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, created = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.materials.count(), 0)
        self.assertEqual(obj.enabled_sections._value, 0)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_dogmas_global(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(
            set(obj.dogma_attributes.values_list("eve_dogma_attribute_id", flat=True)),
            {129, 588},
        )
        self.assertEqual(
            set(obj.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )
        self.assertTrue(obj.enabled_sections.dogmas)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_dogmas_on_demand(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.Section.DOGMAS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(
            set(obj.dogma_attributes.values_list("eve_dogma_attribute_id", flat=True)),
            {129, 588},
        )
        self.assertEqual(
            set(obj.dogma_effects.values_list("eve_dogma_effect_id", flat=True)),
            {1816, 1817},
        )
        self.assertTrue(obj.enabled_sections.dogmas)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_graphics_global(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.eve_graphic_id, 314)
        self.assertTrue(obj.enabled_sections.graphics)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_graphics_on_demand(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.Section.GRAPHICS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.eve_graphic_id, 314)
        self.assertTrue(obj.enabled_sections.graphics)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_market_groups_global(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.eve_market_group_id, 61)
        self.assertTrue(obj.enabled_sections.market_groups)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_create_type_with_market_groups_on_demand(
        self, mock_esi, mock_cache
    ):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.Section.MARKET_GROUPS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.eve_market_group_id, 61)
        self.assertTrue(obj.enabled_sections.market_groups)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", True)
    def test_should_create_type_with_type_materials_global(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        # when
        obj, created = EveType.objects.update_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertEqual(
            set(obj.materials.values_list("material_eve_type_id", flat=True)),
            {34, 35, 36, 37, 38, 39, 40},
        )
        self.assertTrue(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
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
        self.assertEqual(
            set(obj.materials.values_list("material_eve_type_id", flat=True)),
            {34, 35, 36, 37, 38, 39, 40},
        )
        self.assertTrue(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_not_fetch_type_again(self, mock_esi, mock_cache):
        # given
        mock_esi.client = EsiClientStub()
        EveType.objects.update_or_create_esi(id=603)
        # when
        obj, created = EveType.objects.get_or_create_esi(id=603)
        # then
        self.assertEqual(obj.id, 603)
        self.assertFalse(created)
        self.assertEqual(obj.enabled_sections._value, 0)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_fetch_type_again_with_section_on_demand_1(
        self, mock_esi, mock_cache
    ):
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
        self.assertEqual(
            set(obj.materials.values_list("material_eve_type_id", flat=True)),
            {34, 35, 36, 37, 38, 39, 40},
        )
        self.assertTrue(obj.enabled_sections.type_materials)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_TYPE_MATERIALS", False)
    def test_should_fetch_type_again_with_section_on_demand_2(
        self, mock_esi, mock_cache
    ):
        # given
        mock_esi.client = EsiClientStub()
        mock_cache.get.return_value = type_materials_cache_content()
        EveType.objects.update_or_create_esi(
            id=603, enabled_sections=[EveType.Section.TYPE_MATERIALS]
        )
        # when
        obj, created = EveType.objects.get_or_create_esi(
            id=603, enabled_sections=[EveType.Section.GRAPHICS]
        )
        # then
        self.assertEqual(obj.id, 603)
        self.assertFalse(created)
        self.assertEqual(
            set(obj.materials.values_list("material_eve_type_id", flat=True)),
            {34, 35, 36, 37, 38, 39, 40},
        )
        self.assertEqual(obj.eve_graphic_id, 314)
        self.assertTrue(obj.enabled_sections.graphics)
        self.assertTrue(obj.enabled_sections.type_materials)


class EveTypeSection(NoSocketsTestCase):
    def test_should_return_value_as_str(self):
        self.assertEqual(str(EveType.Section.DOGMAS), "dogmas")

    def test_should_return_values(self):
        self.assertEqual(
            list(EveType.Section),
            ["dogmas", "graphics", "market_groups", "type_materials"],
        )


@patch(MANAGERS_PATH + ".esi")
class TestEveSolarSystemWithSections(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_without_sections(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(id=30045339)
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertEqual(obj.enabled_sections._value, 0)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_planets_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339, include_children=True
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.planets)
        self.assertEqual(
            set(obj.eve_planets.values_list("id", flat=True)), {40349467, 40349471}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_planets_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.PLANETS],
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.planets)
        self.assertEqual(
            set(obj.eve_planets.values_list("id", flat=True)), {40349467, 40349471}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stargates_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339, include_children=True
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stargates)
        self.assertEqual(
            set(obj.eve_stargates.values_list("id", flat=True)), {50016284, 50016286}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stargates_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.STARGATES],
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stargates)
        self.assertEqual(
            set(obj.eve_stargates.values_list("id", flat=True)), {50016284, 50016286}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stars_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339, include_children=True
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stars)
        self.assertEqual(obj.eve_star_id, 40349466)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stars_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.STARS],
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stars)
        self.assertEqual(obj.eve_star_id, 40349466)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", True)
    def test_should_create_solar_system_with_stations_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339, include_children=True
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stations)
        self.assertEqual(
            set(obj.eve_stations.values_list("id", flat=True)), {60015068, 60015069}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stations_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.STATIONS],
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stations)
        self.assertEqual(
            set(obj.eve_stations.values_list("id", flat=True)), {60015068, 60015069}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_stargates_on_demand_2(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.STARGATES, EveType.Section.DOGMAS],
        )
        # then
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(obj.enabled_sections.stargates)
        self.assertEqual(
            set(obj.eve_stargates.values_list("id", flat=True)), {50016284, 50016286}
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_planets_moons_asteroid_belts_on_demand(
        self, mock_esi
    ):
        # given
        mock_esi.client = EsiClientStub()
        # when
        solar_system, _ = EveSolarSystem.objects.update_or_create_esi(
            id=30045339,
            include_children=True,
            enabled_sections=[
                EveSolarSystem.Section.PLANETS,
                EvePlanet.Section.ASTEROID_BELTS,
                EvePlanet.Section.MOONS,
            ],
        )
        # then
        self.assertEqual(solar_system.id, 30045339)
        self.assertTrue(solar_system.enabled_sections.planets)
        self.assertEqual(
            set(solar_system.eve_planets.values_list("id", flat=True)),
            {40349467, 40349471},
        )
        planet = solar_system.eve_planets.get(id=40349471)
        self.assertEqual(
            set(planet.eve_asteroid_belts.values_list("id", flat=True)), {40349487}
        )
        self.assertEqual(
            set(planet.eve_moons.values_list("id", flat=True)), {40349472, 40349473}
        )


@patch(MANAGERS_PATH + ".esi")
class TestEveSolarSystemBulkWithSection(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_planets_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.update_or_create_all_esi(include_children=True)
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30001161, 30045339, 30045342, 31000005},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_create_solar_system_with_planets_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.update_or_create_all_esi(
            include_children=True, enabled_sections=[EveSolarSystem.Section.PLANETS]
        )
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30001161, 30045339, 30045342, 31000005},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_get_solar_system_with_planets_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.bulk_get_or_create_esi(
            ids=[30000142, 30045339], include_children=True
        )
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30045339},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_get_all_solar_system_with_planets_on_demand_from_scratch(
        self, mock_esi
    ):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.bulk_get_or_create_esi(
            ids=[30000142, 30045339],
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.PLANETS],
        )
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30045339},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )

    @patch(
        MODELS_PATH + ".EveSolarSystem.objects.update_or_create_esi",
        wraps=EveSolarSystem.objects.update_or_create_esi,
    )
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_get_all_solar_system_with_planets_on_demand(
        self, spy_manager, mock_esi
    ):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.get_or_create_esi(id=30000142)
        EveSolarSystem.objects.bulk_get_or_create_esi(
            ids=[30000142, 30045339],
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.PLANETS],
        )
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30045339},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )
        self.assertEqual(spy_manager.call_count, 3)

    @patch(
        MODELS_PATH + ".EveSolarSystem.objects.update_or_create_esi",
        wraps=EveSolarSystem.objects.update_or_create_esi,
    )
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_should_get_one_and_load_one_solar_system_with_planets(
        self, spy_manager, mock_esi
    ):
        # given
        mock_esi.client = EsiClientStub()
        # when
        EveSolarSystem.objects.get_or_create_esi(
            id=30000142,
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.PLANETS],
        )
        EveSolarSystem.objects.bulk_get_or_create_esi(
            ids=[30000142, 30045339],
            include_children=True,
            enabled_sections=[EveSolarSystem.Section.PLANETS],
        )
        # then
        self.assertEqual(
            set(
                EveSolarSystem.objects.filter(
                    enabled_sections=EveSolarSystem.enabled_sections.planets
                ).values_list("id", flat=True)
            ),
            {30000142, 30045339},
        )
        self.assertEqual(
            set(EvePlanet.objects.values_list("id", flat=True)),
            {40009077, 40349467, 40349471},
        )
        self.assertEqual(spy_manager.call_count, 2)


@patch(MANAGERS_PATH + ".esi")
class TestEvePlanetWithSections(NoSocketsTestCase):
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    def test_should_create_new_instance_without_sections(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EvePlanet.objects.update_or_create_esi(id=40349471)
        # then
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(obj.eve_asteroid_belts.count(), 0)
        self.assertEqual(obj.eve_moons.count(), 0)
        self.assertEqual(obj.enabled_sections._value, 0)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    def test_should_create_new_instance_with_asteroid_belts_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EvePlanet.objects.update_or_create_esi(
            id=40349471, include_children=True
        )
        # then
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(
            set(obj.eve_asteroid_belts.values_list("id", flat=True)), {40349487}
        )
        self.assertEqual(obj.eve_moons.count(), 0)
        self.assertTrue(obj.enabled_sections.asteroid_belts)
        self.assertFalse(obj.enabled_sections.moons)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    def test_should_create_new_instance_with_asteroid_belts_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EvePlanet.objects.update_or_create_esi(
            id=40349471,
            include_children=True,
            enabled_sections=[EvePlanet.Section.ASTEROID_BELTS],
        )
        # then
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(
            set(obj.eve_asteroid_belts.values_list("id", flat=True)), {40349487}
        )
        self.assertEqual(obj.eve_moons.count(), 0)
        self.assertTrue(obj.enabled_sections.asteroid_belts)
        self.assertFalse(obj.enabled_sections.moons)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    def test_should_create_new_instance_with_moons_global(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EvePlanet.objects.update_or_create_esi(
            id=40349471, include_children=True
        )
        # then
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(obj.eve_asteroid_belts.count(), 0)
        self.assertEqual(
            set(obj.eve_moons.values_list("id", flat=True)), {40349472, 40349473}
        )
        self.assertFalse(obj.enabled_sections.asteroid_belts)
        self.assertTrue(obj.enabled_sections.moons)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    def test_should_create_new_instance_with_moons_on_demand(self, mock_esi):
        # given
        mock_esi.client = EsiClientStub()
        # when
        obj, _ = EvePlanet.objects.update_or_create_esi(
            id=40349471,
            include_children=True,
            enabled_sections=[EvePlanet.Section.MOONS],
        )
        # then
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(obj.eve_asteroid_belts.count(), 0)
        self.assertEqual(
            set(obj.eve_moons.values_list("id", flat=True)), {40349472, 40349473}
        )
        self.assertFalse(obj.enabled_sections.asteroid_belts)
        self.assertTrue(obj.enabled_sections.moons)
