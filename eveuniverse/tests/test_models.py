from unittest.mock import patch

from .my_test_data import esi_mock_client
from ..models import (
    EveCategory,
    EveGroup,
    EveType,
    EveMarketGroup,
    EveDogmaAttribute,
    EveDogmaEffect,
)
from ..utils import NoSocketsTestCase


@patch("eveuniverse.managers.esi")
class TestEveDogmaAttribute(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveDogmaAttribute.objects.update_or_create_esi(
            id=271, include_children=False
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 271)
        self.assertEqual(obj.name, "shieldEmDamageResonance")
        self.assertEqual(obj.default_value, 1)
        self.assertEqual(obj.description, "Multiplies EM damage taken by shield")
        self.assertEqual(obj.display_name, "Shield EM Damage Resistance")
        self.assertEqual(obj.icon_id, 1396)
        self.assertTrue(obj.published)
        self.assertEqual(obj.unit_id, 108)


@patch("eveuniverse.managers.esi")
class TestEveDogmaEffect(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveDogmaEffect.objects.update_or_create_esi(
            id=1816, include_children=False
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 1816)
        self.assertEqual(obj.name, "shipShieldEMResistanceCF2")


@patch("eveuniverse.managers.esi")
class TestEveCategory(NoSocketsTestCase):
    def test_when_not_exists_load_object_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveCategory.objects.get_or_create_esi(
            id=6, include_children=False
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_just_return_object(self, mock_esi):
        mock_esi.client = esi_mock_client()

        EveCategory.objects.update_or_create_esi(id=6, include_children=False)

        obj, created = EveCategory.objects.get_or_create_esi(
            id=6, include_children=False
        )
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_can_reload_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, _ = EveCategory.objects.update_or_create_esi(id=6, include_children=False)
        obj.name = "xxx"
        obj.save()

        obj, created = EveCategory.objects.update_or_create_esi(
            id=6, include_children=False
        )
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_can_load_from_esi_including_children(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveCategory.objects.get_or_create_esi(
            id=6, include_children=True
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)


@patch("eveuniverse.managers.esi")
class TestEveType(NoSocketsTestCase):
    def test_when_not_exists_load_object_from_esi(self, mock_esi):
        mock_esi.client = esi_mock_client()

        EveCategory.objects.update_or_create_esi(id=6, include_children=False)
        EveGroup.objects.update_or_create_esi(id=25, include_children=False)

        obj, created = EveType.objects.get_or_create_esi(id=603, include_children=False)
        self.assertTrue(created)
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.name, "Merlin")
        self.assertTrue(obj.published)


@patch("eveuniverse.managers.esi")
class TestEveMarketGroup(NoSocketsTestCase):
    def test_can_fetch_parent_group(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveMarketGroup.objects.get_or_create_esi(
            id=4, include_children=False
        )
        self.assertTrue(created)
        self.assertEqual(obj.name, "Ships")

    def test_can_fetch_group_and_all_parents(self, mock_esi):
        mock_esi.client = esi_mock_client()

        obj, created = EveMarketGroup.objects.get_or_create_esi(
            id=61, include_children=False
        )
        self.assertTrue(created)
        self.assertEqual(obj.name, "Caldari")
        self.assertEqual(obj.parent_market_group.name, "Standard Frigates")
        self.assertEqual(obj.parent_market_group.parent_market_group.name, "Frigates")
        self.assertEqual(
            obj.parent_market_group.parent_market_group.parent_market_group.name,
            "Ships",
        )

