import unittest
from unittest.mock import patch

from bravado.exception import HTTPNotFound

from .my_test_data import esi_mock_client
from ..models import (
    EsiMapping,
    EveAncestry,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveGroup,
    EveType,
    EveMarketGroup,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveRace,
    EveRegion,
    EveTypeDogmaEffect,
    EveTypeDogmaAttribute,
)
from ..utils import NoSocketsTestCase

unittest.util._MAX_LENGTH = 1000
MODULE_PATH = "eveuniverse.models"


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveDogmaAttribute(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveDogmaAttribute.objects.update_or_create_esi(id=271)
        self.assertTrue(created)
        self.assertEqual(obj.id, 271)
        self.assertEqual(obj.name, "shieldEmDamageResonance")
        self.assertEqual(obj.default_value, 1)
        self.assertEqual(obj.description, "Multiplies EM damage taken by shield")
        self.assertEqual(obj.display_name, "Shield EM Damage Resistance")
        self.assertEqual(obj.icon_id, 1396)
        self.assertTrue(obj.published)
        self.assertEqual(obj.eve_unit_id, 108)


@patch("eveuniverse.managers.esi")
class TestEveAncestry(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveAncestry.objects.update_or_create_esi(id=8)
        self.assertTrue(created)
        self.assertEqual(obj.id, 8)
        self.assertEqual(obj.name, "Mercs")
        self.assertEqual(obj.icon_id, 1648)

        self.assertTrue(EveBloodline.objects.filter(id=2).exists())
        self.assertTrue(EveType.objects.filter(id=603).exists())
        self.assertTrue(EveRace.objects.filter(id=1).exists())

    def test_raise_404_exception_when_object_not_found(self, mock_esi):
        mock_esi.client = esi_mock_client()

        with self.assertRaises(HTTPNotFound):
            EveAncestry.objects.update_or_create_esi(id=1)


@patch("eveuniverse.managers.esi")
class TestEveRace(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveRace.objects.update_or_create_esi(id=1)
        self.assertTrue(created)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.name, "Caldari")
        self.assertEqual(obj.alliance_id, 500001)


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveDogmaEffect(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveDogmaEffect.objects.update_or_create_esi(id=1816)
        self.assertTrue(created)
        self.assertEqual(obj.id, 1816)
        self.assertEqual(obj.name, "shipShieldEMResistanceCF2")


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveCategory(NoSocketsTestCase):
    def test_when_not_exists_load_object_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveCategory.objects.get_or_create_esi(id=6)
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_just_return_object(self, mock_esi):
        mock_esi.client = esi_mock_client()

        EveCategory.objects.update_or_create_esi(id=6)

        obj, created = EveCategory.objects.get_or_create_esi(id=6)
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_can_reload_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, _ = EveCategory.objects.update_or_create_esi(id=6)
        obj.name = "xxx"
        obj.save()

        obj, created = EveCategory.objects.update_or_create_esi(id=6)
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_can_load_from_esi_including_children(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveCategory.objects.get_or_create_esi(
            id=6, include_children=True, wait_for_children=True
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)


@patch("eveuniverse.managers.esi")
class TestEveType(NoSocketsTestCase):
    @patch("eveuniverse.managers.esi")
    def setUp(self, mock_esi):
        mock_esi.client = esi_mock_client()

        EveCategory.objects.update_or_create_esi(id=6)
        EveGroup.objects.update_or_create_esi(id=25)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    def test_can_create_type_from_esi_including_dogmas(self, mock_esi):
        mock_esi.client = esi_mock_client()

        # type
        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertEqual(eve_type.name, "Merlin")
        self.assertTrue(eve_type.published)

        # market group
        self.assertTrue(EveMarketGroup.objects.filter(id=61).exists())

        # dogmas
        self.assertTrue(EveDogmaAttribute.objects.filter(id=129).exists())
        self.assertTrue(EveDogmaAttribute.objects.filter(id=588).exists())
        self.assertTrue(EveDogmaEffect.objects.filter(id=1816).exists())
        self.assertTrue(EveDogmaEffect.objects.filter(id=1817).exists())

        # type dogmas
        obj = EveTypeDogmaAttribute.objects.get(
            eve_type=eve_type, eve_dogma_attribute_id=129
        )
        self.assertEqual(obj.value, 12)
        obj = EveTypeDogmaAttribute.objects.get(
            eve_type=eve_type, eve_dogma_attribute_id=588
        )
        self.assertEqual(obj.value, 5)
        obj = EveTypeDogmaEffect.objects.get(
            eve_type=eve_type, eve_dogma_effect_id=1816
        )
        self.assertFalse(obj.is_default)
        obj = EveTypeDogmaEffect.objects.get(
            eve_type=eve_type, eve_dogma_effect_id=1817
        )
        self.assertTrue(obj.is_default)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    def test_when_disabled_can_create_type_from_esi_excluding_dogmas(self, mock_esi):
        mock_esi.client = esi_mock_client()

        # type
        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertEqual(eve_type.name, "Merlin")
        self.assertTrue(eve_type.published)

        # market group
        self.assertTrue(EveMarketGroup.objects.filter(id=61).exists())

        # dogmas
        self.assertFalse(EveDogmaAttribute.objects.filter(id=129).exists())
        self.assertFalse(EveDogmaAttribute.objects.filter(id=588).exists())
        self.assertFalse(EveDogmaEffect.objects.filter(id=1816).exists())
        self.assertFalse(EveDogmaEffect.objects.filter(id=1817).exists())

        # type dogmas
        self.assertEqual(EveTypeDogmaAttribute.objects.count(), 0)
        self.assertEqual(EveTypeDogmaEffect.objects.count(), 0)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_when_disabled_can_create_type_from_esi_excluding_market_groups(
        self, mock_esi
    ):
        mock_esi.client = esi_mock_client()

        # type
        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertEqual(eve_type.name, "Merlin")
        self.assertTrue(eve_type.published)

        # market group
        self.assertFalse(EveMarketGroup.objects.filter(id=61).exists())

        # dogmas
        self.assertTrue(EveDogmaAttribute.objects.filter(id=129).exists())
        self.assertTrue(EveDogmaAttribute.objects.filter(id=588).exists())
        self.assertTrue(EveDogmaEffect.objects.filter(id=1816).exists())
        self.assertTrue(EveDogmaEffect.objects.filter(id=1817).exists())

        # type dogmas
        self.assertGreater(EveTypeDogmaAttribute.objects.count(), 0)
        self.assertGreater(EveTypeDogmaEffect.objects.count(), 0)


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveMarketGroup(NoSocketsTestCase):
    def test_can_fetch_parent_group(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveMarketGroup.objects.get_or_create_esi(id=4)
        self.assertTrue(created)
        self.assertEqual(obj.name, "Ships")

    def test_can_fetch_group_and_all_parents(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveMarketGroup.objects.get_or_create_esi(id=61)
        self.assertTrue(created)
        self.assertEqual(obj.name, "Caldari")
        self.assertEqual(obj.parent_market_group.name, "Standard Frigates")
        self.assertEqual(obj.parent_market_group.parent_market_group.name, "Frigates")
        self.assertEqual(
            obj.parent_market_group.parent_market_group.parent_market_group.name,
            "Ships",
        )


class TestEsiMapping(NoSocketsTestCase):

    maxDiff = None

    def test_single_pk(self):
        mapping = EveCategory.esi_mapping()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="category_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
            ),
        )
        self.assertEqual(
            mapping["published"],
            EsiMapping(
                esi_name="published",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )

    def test_with_fk(self):
        mapping = EveConstellation.esi_mapping()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="constellation_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
            ),
        )
        self.assertEqual(
            mapping["eve_region"],
            EsiMapping(
                esi_name="region_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveRegion,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )

    def test_optional_fields(self):
        mapping = EveAncestry.esi_mapping()
        self.assertEqual(len(mapping.keys()), 6)
        self.assertEqual(
            mapping["id"],
            EsiMapping(
                esi_name="id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["name"],
            EsiMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
            ),
        )
        self.assertEqual(
            mapping["eve_bloodline"],
            EsiMapping(
                esi_name="bloodline_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveBloodline,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["description"],
            EsiMapping(
                esi_name="description",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
            ),
        )
        self.assertEqual(
            mapping["icon_id"],
            EsiMapping(
                esi_name="icon_id",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["short_description"],
            EsiMapping(
                esi_name="short_description",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
            ),
        )

    def test_inline_model(self):
        mapping = EveTypeDogmaEffect.esi_mapping()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["eve_type"],
            EsiMapping(
                esi_name="eve_type",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveType,
                is_parent_fk=True,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["eve_dogma_effect"],
            EsiMapping(
                esi_name="effect_id",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveDogmaEffect,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )
        self.assertEqual(
            mapping["is_default"],
            EsiMapping(
                esi_name="is_default",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
            ),
        )

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_EveType_mapping(self):
        mapping = EveType.esi_mapping()
        self.assertSetEqual(
            set(mapping.keys()),
            {
                "id",
                "name",
                "capacity",
                "eve_group",
                "graphic_id",
                "icon_id",
                "eve_market_group",
                "mass",
                "packaged_volume",
                "portion_size",
                "radius",
                "published",
                "volume",
            },
        )

