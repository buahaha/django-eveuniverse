from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings

from .my_test_data import EsiClientStub
from ..models import (
    EveCategory,
    EveDogmaAttribute,
    EveGroup,
    EveRegion,
    EveConstellation,
    EveSolarSystem,
    EveType,
)
from ..tasks import (
    load_eve_object,
    load_map,
    load_ship_types,
    load_structure_types,
    update_or_create_eve_object,
    update_or_create_inline_object,
    create_eve_entities,
    update_unresolved_eve_entities,
    update_market_prices,
)
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

    @patch("eveuniverse.managers.esi")
    def test_update_or_create_inline_object(self, mock_esi):
        mock_esi.client = EsiClientStub()
        eve_type, _ = EveType.objects.update_or_create_esi(id=603)

        update_or_create_inline_object(
            parent_obj_id=eve_type.id,
            parent_fk="eve_type",
            eve_data_obj={"attribute_id": 588, "value": 5},
            other_pk_info={
                "esi_name": "attribute_id",
                "is_fk": True,
                "name": "eve_dogma_attribute",
            },
            parent2_model_name="EveDogmaAttribute",
            inline_model_name="EveTypeDogmaAttribute",
            parent_model_name=type(eve_type).__name__,
        )
        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=588)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 5)

    @patch(MODULE_PATH + ".EveEntity.objects.bulk_create_esi")
    def test_create_eve_entities(self, mock_bulk_create_esi):
        create_eve_entities([1, 2, 3])
        self.assertTrue(mock_bulk_create_esi.called)
        args, _ = mock_bulk_create_esi.call_args
        self.assertListEqual(args[0], [1, 2, 3])

    @patch(MODULE_PATH + ".EveEntity.objects.bulk_update_new_esi")
    def test_update_unresolved_eve_entities(self, mock_bulk_update_new_esi):
        update_unresolved_eve_entities()
        self.assertTrue(mock_bulk_update_new_esi.called)

    @patch(MODULE_PATH + ".EveMarketPrice.objects.update_from_esi")
    def test_update_market_prices(self, mock_update_from_esi):
        update_market_prices()
        self.assertTrue(mock_update_from_esi.called)


@override_settings(CELERY_ALWAYS_EAGER=True)
@patch(MODULE_PATH + ".esi")
@patch("eveuniverse.managers.esi")
class TestLoadData(TestCase):
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

    def test_load_ship_types(self, mock_esi_1, mock_esi_2):
        mock_esi_1.client = EsiClientStub()
        mock_esi_2.client = EsiClientStub()
        load_ship_types()

        self.assertTrue(EveCategory.objects.filter(id=6).exists())
        for id in [25, 26]:
            self.assertTrue(EveGroup.objects.filter(id=id).exists())

        for id in [603, 608, 621, 626]:
            self.assertTrue(EveType.objects.filter(id=id).exists())

    def test_load_structure_types(self, mock_esi_1, mock_esi_2):
        mock_esi_1.client = EsiClientStub()
        mock_esi_2.client = EsiClientStub()
        load_structure_types()

        self.assertTrue(EveCategory.objects.filter(id=65).exists())
        for id in [1404]:
            self.assertTrue(EveGroup.objects.filter(id=id).exists())

        for id in [35825]:
            self.assertTrue(EveType.objects.filter(id=id).exists())
