from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test.utils import override_settings

from ..models import EveCategory, EveGroup, EveType
from ..utils import NoSocketsTestCase
from .testdata.esi import EsiClientStub

PACKAGE_PATH = "eveuniverse.management.commands"


@patch(PACKAGE_PATH + ".eveuniverse_load_data.is_esi_online", lambda: True)
@patch(PACKAGE_PATH + ".eveuniverse_load_data.get_input")
class TestLoadCommand(NoSocketsTestCase):
    def setUp(self) -> None:
        self.out = StringIO()

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_map")
    def test_load_data_map(self, mock_load_map, mock_get_input):
        mock_get_input.return_value = "y"

        call_command("eveuniverse_load_data", "map", stdout=self.out)
        self.assertTrue(mock_load_map.delay.called)

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_ship_types")
    def test_load_data_ship_types(self, mock_load_ship_types, mock_get_input):
        mock_get_input.return_value = "y"

        call_command("eveuniverse_load_data", "ships", stdout=self.out)
        self.assertTrue(mock_load_ship_types.delay.called)

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_structure_types")
    def test_load_data_structure_types(self, mock_load_structure_types, mock_get_input):
        mock_get_input.return_value = "y"

        call_command("eveuniverse_load_data", "structures", stdout=self.out)
        self.assertTrue(mock_load_structure_types.delay.called)

    @patch(PACKAGE_PATH + ".eveuniverse_load_data.load_map")
    def test_can_abort(self, mock_load_map, mock_get_input):
        mock_get_input.return_value = "n"

        call_command("eveuniverse_load_data", "map", stdout=self.out)
        self.assertFalse(mock_load_map.delay.called)


@override_settings(CELERY_ALWAYS_EAGER=True)
@patch("eveuniverse.managers.esi")
@patch(PACKAGE_PATH + ".eveuniverse_load_types.is_esi_online", lambda: True)
@patch(PACKAGE_PATH + ".eveuniverse_load_types.get_input")
class TestLoadTypes(NoSocketsTestCase):
    def setUp(self) -> None:
        self.out = StringIO()

    def test_load_one_type(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types", "dummy_app", "--type_id", "603", stdout=self.out
        )
        obj = EveType.objects.get(id=603)
        self.assertEqual(obj.dogma_attributes.count(), 0)
        self.assertEqual(obj.dogma_effects.count(), 0)

    def test_load_multiple_types(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            "--type_id",
            "1529",
            "--type_id",
            "35825",
            stdout=self.out,
        )
        self.assertTrue(EveType.objects.filter(id=1529).exists())
        self.assertTrue(EveType.objects.filter(id=35825).exists())

    def test_load_multiple_combined(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            "--category_id",
            "65",
            stdout=self.out,
        )
        self.assertTrue(EveCategory.objects.filter(id=65).exists())
        self.assertTrue(EveGroup.objects.filter(id=1404).exists())
        self.assertTrue(EveType.objects.filter(id=35825).exists())

    def test_can_handle_no_input(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            stdout=self.out,
        )

    def test_can_abort(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "n"

        call_command(
            "eveuniverse_load_types", "dummy_app", "--type_id", "35825", stdout=self.out
        )
        self.assertFalse(EveType.objects.filter(id=35825).exists())

    def test_load_one_type_with_dogma(self, mock_get_input, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            "--type_id_with_dogma",
            "603",
            stdout=self.out,
        )
        obj = EveType.objects.get(id=603)
        self.assertEqual(obj.dogma_attributes.count(), 2)
        self.assertEqual(obj.dogma_effects.count(), 2)


@override_settings(CELERY_ALWAYS_EAGER=True)
@patch("eveuniverse.managers.esi")
@patch(PACKAGE_PATH + ".eveuniverse_load_types.is_esi_online")
@patch(PACKAGE_PATH + ".eveuniverse_load_types.get_input")
class TestLoadTypesEsiCheck(NoSocketsTestCase):
    def setUp(self) -> None:
        self.out = StringIO()

    def test_checks_esi_by_default(self, mock_get_input, mock_is_esi_online, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            "--type_id",
            "603",
            stdout=self.out,
        )
        self.assertTrue(EveType.objects.filter(id=603).exists())
        self.assertTrue(mock_is_esi_online.called)

    def test_can_disable_esi_check(self, mock_get_input, mock_is_esi_online, mock_esi):
        mock_esi.client = EsiClientStub()
        mock_get_input.return_value = "y"

        call_command(
            "eveuniverse_load_types",
            "dummy_app",
            "--type_id",
            "603",
            "--disable_esi_check",
            stdout=self.out,
        )
        self.assertTrue(EveType.objects.filter(id=603).exists())
        self.assertFalse(mock_is_esi_online.called)
