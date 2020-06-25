import unittest
from unittest.mock import patch

from bravado.exception import HTTPNotFound

from ..models import (
    EsiMapping,
    EveAncestry,
    EveAsteroidBelt,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveFaction,
    EveGraphic,
    EveGroup,
    EveMarketGroup,
    EveMoon,
    EvePlanet,
    EveRace,
    EveRegion,
    EveSolarSystem,
    EveStar,
    EveStargate,
    EveStation,
    EveType,
    EveTypeDogmaEffect,
    EveUnit,
)
from ..utils import NoSocketsTestCase
from .my_test_data import EsiMockClient

unittest.util._MAX_LENGTH = 1000
MODULE_PATH = "eveuniverse.models"


@patch("eveuniverse.managers.esi")
class TestEveAncestry(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveAncestry.objects.update_or_create_esi(id=8)
        self.assertTrue(created)
        self.assertEqual(obj.id, 8)
        self.assertEqual(obj.name, "Mercs")
        self.assertEqual(obj.icon_id, 1648)
        self.assertEqual(obj.eve_bloodline, EveBloodline.objects.get(id=2))
        self.assertEqual(
            obj.short_description,
            "Guns for hire that are always available to the highest bidder.",
        )

    def test_raise_404_exception_when_object_not_found(self, mock_esi):
        mock_esi.client = EsiMockClient()

        with self.assertRaises(HTTPNotFound):
            EveAncestry.objects.update_or_create_esi(id=1)


@patch("eveuniverse.managers.esi")
class TestEveAsteroidBelt(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveAsteroidBelt.objects.update_or_create_esi(id=40349487)
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349487)
        self.assertEqual(obj.name, "Enaluri III - Asteroid Belt 1")
        self.assertEqual(obj.position_x, -214506997304.68906)
        self.assertEqual(obj.position_y, -41236109278.05316)
        self.assertEqual(obj.position_z, 219234300596.24887)
        self.assertEqual(obj.eve_planet, EvePlanet.objects.get(id=40349471))


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveCategory(NoSocketsTestCase):
    def test_when_not_exists_load_object_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveCategory.objects.get_or_create_esi(id=6)
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_just_return_object(self, mock_esi):
        mock_esi.client = EsiMockClient()

        EveCategory.objects.update_or_create_esi(id=6)

        obj, created = EveCategory.objects.get_or_create_esi(id=6)
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_when_exists_can_reload_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, _ = EveCategory.objects.update_or_create_esi(id=6)
        obj.name = "xxx"
        obj.save()

        obj, created = EveCategory.objects.update_or_create_esi(id=6)
        self.assertFalse(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)

    def test_can_load_from_esi_including_children(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveCategory.objects.get_or_create_esi(
            id=6, include_children=True, wait_for_children=True
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 6)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)


@patch("eveuniverse.managers.esi")
class TestEveConstellation(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveConstellation.objects.update_or_create_esi(id=20000785)
        self.assertTrue(created)
        self.assertEqual(obj.id, 20000785)
        self.assertEqual(obj.name, "Ishaga")
        self.assertEqual(obj.position_x, -222687068034733630)
        self.assertEqual(obj.position_y, 108368351346494510)
        self.assertEqual(obj.position_z, 136029596082308480)
        self.assertEqual(obj.eve_region, EveRegion.objects.get(id=10000069))


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveDogmaAttribute(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

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


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveDogmaEffect(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveDogmaEffect.objects.update_or_create_esi(id=1816)
        self.assertTrue(created)
        self.assertEqual(obj.id, 1816)
        self.assertEqual(obj.name, "shipShieldEMResistanceCF2")
        self.assertEqual(obj.display_name, "")
        self.assertEqual(obj.effect_category, 0)
        self.assertEqual(obj.icon_id, 0)
        modifiers = obj.modifiers.first()
        self.assertEqual(modifiers.domain, "shipID")
        self.assertEqual(modifiers.func, "ItemModifier")
        self.assertEqual(
            modifiers.modified_attribute, EveDogmaAttribute.objects.get(id=271)
        )
        self.assertEqual(
            modifiers.modifying_attribute, EveDogmaAttribute.objects.get(id=463),
        )
        self.assertEqual(modifiers.operator, 6)


@patch("eveuniverse.managers.esi")
class TestEveFaction(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveFaction.objects.update_or_create_esi(id=500001)
        self.assertTrue(created)
        self.assertEqual(obj.id, 500001)
        self.assertEqual(obj.name, "Caldari State")
        self.assertTrue(obj.is_unique)
        self.assertEqual(obj.militia_corporation_id, 1000180)
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))
        self.assertEqual(obj.size_factor, 5)
        self.assertEqual(obj.station_count, 1503)
        self.assertEqual(obj.station_system_count, 503)


@patch("eveuniverse.managers.esi")
class TestEveGraphic(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveGraphic.objects.update_or_create_esi(id=314)
        self.assertTrue(created)
        self.assertEqual(obj.id, 314)
        self.assertEqual(obj.sof_dna, "cf7_t1:caldaribase:caldari")
        self.assertEqual(obj.sof_fation_name, "caldaribase")
        self.assertEqual(obj.sof_hull_name, "cf7_t1")
        self.assertEqual(obj.sof_race_name, "caldari")


@patch("eveuniverse.managers.esi")
class TestEveGroup(NoSocketsTestCase):
    def test_can_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveGroup.objects.update_or_create_esi(id=10)
        self.assertTrue(created)
        self.assertEqual(obj.id, 10)
        self.assertEqual(obj.name, "Stargate")
        self.assertFalse(obj.published)


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
@patch("eveuniverse.managers.esi")
class TestEveMarketGroup(NoSocketsTestCase):
    def test_can_fetch_parent_group(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveMarketGroup.objects.get_or_create_esi(id=4)
        self.assertTrue(created)
        self.assertEqual(obj.name, "Ships")

    def test_can_fetch_group_and_all_parents(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveMarketGroup.objects.get_or_create_esi(id=61)
        self.assertTrue(created)
        self.assertEqual(obj.name, "Caldari")
        self.assertEqual(obj.parent_market_group.name, "Standard Frigates")
        self.assertEqual(obj.parent_market_group.parent_market_group.name, "Frigates")
        self.assertEqual(
            obj.parent_market_group.parent_market_group.parent_market_group.name,
            "Ships",
        )


@patch("eveuniverse.managers.esi")
class TestEveMoon(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveMoon.objects.update_or_create_esi(id=40349468)
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349468)
        self.assertEqual(obj.name, "Enaluri I - Moon 1")
        self.assertEqual(obj.position_x, -79612836383.01112)
        self.assertEqual(obj.position_y, -1951529197.9895465)
        self.assertEqual(obj.position_z, 48035834113.70182)
        self.assertEqual(obj.eve_planet, EvePlanet.objects.get(id=40349467))


@patch("eveuniverse.managers.esi")
class TestEvePlanet(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EvePlanet.objects.update_or_create_esi(id=40349467)
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349467)
        self.assertEqual(obj.name, "Enaluri I")
        self.assertEqual(obj.position_x, -79928787523.97133)
        self.assertEqual(obj.position_y, -1951674993.3224173)
        self.assertEqual(obj.position_z, 48099232021.23506)
        self.assertEqual(obj.eve_type, EveType.objects.get(id=2016))
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    def test_create_from_esi_with_children_1(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EvePlanet.objects.update_or_create_esi(
            id=40349467, include_children=True,
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349467)
        self.assertEqual(obj.name, "Enaluri I")
        self.assertEqual(obj.position_x, -79928787523.97133)
        self.assertEqual(obj.position_y, -1951674993.3224173)
        self.assertEqual(obj.position_z, 48099232021.23506)
        self.assertEqual(obj.eve_type, EveType.objects.get(id=2016))
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))

        self.assertTrue(EveMoon.objects.filter(id=40349468).exists())

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    def test_create_from_esi_with_children_2(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EvePlanet.objects.update_or_create_esi(
            id=40349471, include_children=True,
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(obj.name, "Enaluri III")
        self.assertEqual(obj.eve_type, EveType.objects.get(id=13))
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))

        self.assertTrue(EveAsteroidBelt.objects.filter(id=40349487).exists())
        self.assertTrue(EveMoon.objects.filter(id=40349472).exists())
        self.assertTrue(EveMoon.objects.filter(id=40349473).exists())

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    def test_create_from_esi_with_children_2_when_disabled(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EvePlanet.objects.update_or_create_esi(
            id=40349471, include_children=True,
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349471)
        self.assertEqual(obj.name, "Enaluri III")
        self.assertEqual(obj.eve_type, EveType.objects.get(id=13))
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))

        self.assertFalse(EveAsteroidBelt.objects.filter(id=40349487).exists())
        self.assertFalse(EveMoon.objects.filter(id=40349472).exists())
        self.assertFalse(EveMoon.objects.filter(id=40349473).exists())


@patch("eveuniverse.managers.esi")
class TestEveRace(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveRace.objects.update_or_create_esi(id=1)
        self.assertTrue(created)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.name, "Caldari")
        self.assertEqual(obj.alliance_id, 500001)


@patch("eveuniverse.managers.esi")
class TestEveRegion(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveRegion.objects.update_or_create_esi(id=10000069)
        self.assertTrue(created)
        self.assertEqual(obj.id, 10000069)
        self.assertEqual(obj.name, "Black Rise")


@patch("eveuniverse.managers.esi")
class TestEveSolarSystem(NoSocketsTestCase):
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_create_from_esi_minimal(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveSolarSystem.objects.update_or_create_esi(id=30045339)
        self.assertTrue(created)
        self.assertEqual(obj.id, 30045339)
        self.assertEqual(obj.name, "Enaluri")
        self.assertEqual(
            obj.eve_constellation, EveConstellation.objects.get(id=20000785)
        )
        self.assertEqual(obj.position_x, -227875173313944580)
        self.assertEqual(obj.position_y, 104688385699531790)
        self.assertEqual(obj.position_z, 120279417692650270)
        self.assertEqual(obj.security_status, 0.3277980387210846)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    def test_create_from_esi_with_stars(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveSolarSystem.objects.update_or_create_esi(id=30045339)
        self.assertTrue(created)
        self.assertEqual(obj.id, 30045339)
        self.assertEqual(obj.eve_star, EveStar.objects.get(id=40349466))

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STATIONS", True)
    def test_create_from_esi_with_stations(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveSolarSystem.objects.update_or_create_esi(
            id=30045339, include_children=True
        )
        self.assertTrue(created)
        self.assertEqual(obj.id, 30045339)

        self.assertTrue(EveStation.objects.filter(id=60015068).exists())


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch("eveuniverse.managers.esi")
class TestEveStar(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveStar.objects.update_or_create_esi(id=40349466)
        self.assertTrue(created)
        self.assertEqual(obj.id, 40349466)
        self.assertEqual(obj.name, "Enaluri - Star")
        self.assertEqual(obj.luminosity, 0.02542000077664852)
        self.assertEqual(obj.radius, 590000000)
        self.assertEqual(obj.spectral_class, "M6 V")
        self.assertEqual(obj.temperature, 2385)
        self.assertEqual(obj.eve_type, EveType.objects.get(id=3800))


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch("eveuniverse.managers.esi")
class TestEveStargate(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveStargate.objects.get_or_create_esi(id=50016284)
        self.assertTrue(created)
        self.assertEqual(obj.id, 50016284)
        self.assertEqual(obj.name, "Stargate (Akidagi)")
        self.assertEqual(obj.position_x, 4845263708160)
        self.assertEqual(obj.position_y, 97343692800)
        self.assertEqual(obj.position_z, 3689037127680)
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))
        self.assertEqual(obj.eve_type, EveType.objects.get(id=16))
        self.assertIsNone(obj.destination_eve_stargate)
        self.assertIsNone(obj.destination_eve_solar_system)

    def test_create_from_esi_2nd_gate(self, mock_esi):
        mock_esi.client = EsiMockClient()

        akidagi, _ = EveStargate.objects.get_or_create_esi(id=50016284)
        self.assertEqual(akidagi.id, 50016284)
        enaluri, _ = EveStargate.objects.get_or_create_esi(id=50016283)
        self.assertEqual(enaluri.id, 50016283)
        akidagi.refresh_from_db()

        self.assertEqual(enaluri.destination_eve_stargate, akidagi)
        self.assertEqual(akidagi.destination_eve_stargate, enaluri)

        self.assertEqual(
            enaluri.destination_eve_solar_system,
            EveSolarSystem.objects.get(id=30045339),
        )
        self.assertEqual(
            akidagi.destination_eve_solar_system,
            EveSolarSystem.objects.get(id=30045342),
        )


@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_STATIONS", True)
@patch("eveuniverse.managers.esi")
class TestEveStation(NoSocketsTestCase):
    def test_create_from_esi(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveStation.objects.update_or_create_esi(id=60015068)
        self.assertTrue(created)
        self.assertEqual(obj.id, 60015068)
        self.assertEqual(obj.name, "Enaluri V - State Protectorate Assembly Plant")
        self.assertEqual(obj.max_dockable_ship_volume, 50000000)
        self.assertEqual(obj.office_rental_cost, 118744)
        self.assertEqual(obj.owner_id, 1000180)
        self.assertEqual(obj.position_x, 96519659520)
        self.assertEqual(obj.position_y, 65249280)
        self.assertEqual(obj.position_z, 976627507200)
        self.assertEqual(obj.reprocessing_efficiency, 0.5)
        self.assertEqual(obj.reprocessing_stations_take, 0.025)
        self.assertEqual(obj.eve_race, EveRace.objects.get(id=1))
        self.assertEqual(obj.eve_type, EveType.objects.get(id=1529))
        self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))

        self.assertEqual(
            set(obj.services.values_list("name", flat=True)),
            set(
                [
                    "bounty-missions",
                    "courier-missions",
                    "reprocessing-plant",
                    "market",
                    "repair-facilities",
                    "factory",
                    "fitting",
                    "news",
                    "insurance",
                    "docking",
                    "office-rental",
                    "loyalty-point-store",
                    "navy-offices",
                    "security-offices",
                ]
            ),
        )


@patch("eveuniverse.managers.esi")
class TestEveType(NoSocketsTestCase):
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    def test_can_create_type_from_esi_excluding_all(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(obj.id, 603)
        self.assertEqual(obj.name, "Merlin")
        self.assertEqual(obj.capacity, 150)
        self.assertEqual(obj.eve_group, EveGroup.objects.get(id=25))
        self.assertEqual(obj.mass, 997000)
        self.assertEqual(obj.packaged_volume, 2500)
        self.assertEqual(obj.portion_size, 1)
        self.assertTrue(obj.published)
        self.assertEqual(obj.radius, 39)
        self.assertEqual(obj.volume, 16500)
        self.assertIsNone(obj.eve_graphic)
        self.assertIsNone(obj.eve_market_group)
        self.assertEqual(obj.dogma_attributes.count(), 0)
        self.assertEqual(obj.dogma_effects.count(), 0)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    def test_can_create_type_from_esi_including_dogmas(self, mock_esi):
        mock_esi.client = EsiMockClient()

        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertTrue(eve_type.eve_graphic, EveGraphic.objects.get(id=314))
        self.assertTrue(eve_type.eve_market_group, EveMarketGroup.objects.get(id=61))

        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=588)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 5)
        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=129)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 12)

        dogma_effect_1 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1816)
        ).first()
        self.assertFalse(dogma_effect_1.is_default)
        dogma_effect_2 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1817)
        ).first()
        self.assertTrue(dogma_effect_2.is_default)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    def test_when_disabled_can_create_type_from_esi_excluding_dogmas(self, mock_esi):
        mock_esi.client = EsiMockClient()

        obj, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(obj.id, 603)
        self.assertTrue(obj.eve_market_group, EveMarketGroup.objects.get(id=61))
        self.assertEqual(obj.dogma_attributes.count(), 0)
        self.assertEqual(obj.dogma_effects.count(), 0)

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_when_disabled_can_create_type_from_esi_excluding_market_groups(
        self, mock_esi
    ):
        mock_esi.client = EsiMockClient()

        eve_type, created = EveType.objects.get_or_create_esi(id=603)
        self.assertTrue(created)
        self.assertEqual(eve_type.id, 603)
        self.assertIsNone(eve_type.eve_market_group)

        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=588)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 5)
        dogma_attribute_1 = eve_type.dogma_attributes.filter(
            eve_dogma_attribute=EveDogmaAttribute.objects.get(id=129)
        ).first()
        self.assertEqual(dogma_attribute_1.value, 12)

        dogma_effect_1 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1816)
        ).first()
        self.assertFalse(dogma_effect_1.is_default)
        dogma_effect_2 = eve_type.dogma_effects.filter(
            eve_dogma_effect=EveDogmaEffect.objects.get(id=1817)
        ).first()
        self.assertTrue(dogma_effect_2.is_default)


class TestEveUnit(NoSocketsTestCase):
    def test_get_object(self):
        obj = EveUnit.objects.get(id=10)
        self.assertEqual(obj.id, 10)
        self.assertEqual(obj.name, "Speed")


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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
            ),
        )

    def test_with_fk(self):
        mapping = EveConstellation.esi_mapping()
        self.assertEqual(len(mapping.keys()), 6)
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_x"],
            EsiMapping(
                esi_name=("position", "x"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_y"],
            EsiMapping(
                esi_name=("position", "y"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_z"],
            EsiMapping(
                esi_name=("position", "z"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
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
                create_related=True,
            ),
        )

    @patch(MODULE_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", True)
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
                "eve_graphic",
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
