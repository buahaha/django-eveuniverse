from collections import namedtuple
import logging

from django.db import models

from . import __title__
from .app_settings import (
    EVEUNIVERSE_LOAD_DOGMAS,
    EVEUNIVERSE_LOAD_MARKET_GROUPS,
    EVEUNIVERSE_LOAD_ASTEROID_BELTS,
    EVEUNIVERSE_LOAD_MOONS,
    EVEUNIVERSE_LOAD_PLANETS,
    EVEUNIVERSE_LOAD_STARGATES,
    EVEUNIVERSE_LOAD_STATIONS,
)

from .managers import (
    EveUniverseBaseModelManager,
    EveUniverseEntityModelManager,
)
from .utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)

NAMES_MAX_LENGTH = 100


EsiMapping = namedtuple(
    "EsiMapping",
    [
        "esi_name",
        "is_optional",
        "is_pk",
        "is_fk",
        "related_model",
        "is_parent_fk",
        "is_charfield",
    ],
)


class EveUniverseBaseModel(models.Model):
    """Base properties and features"""

    objects = EveUniverseBaseModelManager()

    class Meta:
        abstract = True

    @classmethod
    def esi_mapping(cls) -> dict:
        field_mappings = cls._eve_universe_meta_attr("field_mappings")
        functional_pk = cls._eve_universe_meta_attr("functional_pk")
        parent_fk = cls._eve_universe_meta_attr("parent_fk")
        mapping = dict()
        for field in [
            field
            for field in cls._meta.get_fields()
            if not field.auto_created
            and field.name != "last_updated"
            and field.name not in cls._disabled_fields()
            and not field.many_to_many
        ]:
            if field_mappings and field.name in field_mappings:
                esi_name = field_mappings[field.name]
            else:
                esi_name = field.name

            if field.primary_key is True:
                is_pk = True
                esi_name = cls.esi_pk()
            elif functional_pk and field.name in functional_pk:
                is_pk = True
            else:
                is_pk = False

            if parent_fk and is_pk and field.name in parent_fk:
                is_parent_fk = True
            else:
                is_parent_fk = False

            if isinstance(field, models.ForeignKey):
                is_fk = True
                related_model = field.related_model
            else:
                is_fk = False
                related_model = None

            mapping[field.name] = EsiMapping(
                esi_name=esi_name,
                is_optional=field.has_default(),
                is_pk=is_pk,
                is_fk=is_fk,
                related_model=related_model,
                is_parent_fk=is_parent_fk,
                is_charfield=isinstance(field, (models.CharField, models.TextField)),
            )

        return mapping

    @classmethod
    def _disabled_fields(cls) -> set:
        """returns name of fields that must not be loaded from ESI"""
        return {}

    @classmethod
    def _eve_universe_meta_attr(cls, attr_name: str, is_mandatory: bool = False):
        """returns value of an attribute from EveUniverseMeta or None"""
        if not hasattr(cls, "EveUniverseMeta"):
            raise ValueError("EveUniverseMeta not defined for class %s" % cls.__name__)

        if hasattr(cls.EveUniverseMeta, attr_name):
            value = getattr(cls.EveUniverseMeta, attr_name)
        else:
            value = None
            if is_mandatory:
                raise ValueError(
                    "Mandatory attribute EveUniverseMeta.%s not defined "
                    "for class %s" % (attr_name, cls.__name__)
                )
        return value


class EveUniverseEntityModel(EveUniverseBaseModel):
    """Eve Universe Entity model
    
    Entity models are normal Eve entities that have a dedicated ESI endpoint
    """

    id = models.PositiveIntegerField(primary_key=True, help_text="Eve Online ID")
    name = models.CharField(
        max_length=NAMES_MAX_LENGTH, default="", help_text="Eve Online name"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this object was last updated from ESI",
        db_index=True,
    )

    objects = EveUniverseEntityModelManager()

    class Meta:
        abstract = True

    def __repr__(self):
        return "{}(id={}, name='{}')".format(
            self.__class__.__name__, self.id, self.name
        )

    def __str__(self):
        return self.name

    @classmethod
    def esi_pk(cls) -> str:
        """returns the name of the pk column on ESI that must exist"""
        return cls._eve_universe_meta_attr("esi_pk", is_mandatory=True)

    @classmethod
    def esi_route_category(cls) -> str:
        return cls._esi_path()[0]

    @classmethod
    def esi_route_method(cls) -> str:
        return cls._esi_path()[1]

    @classmethod
    def _esi_path(cls) -> tuple:
        path = cls._eve_universe_meta_attr("esi_path", is_mandatory=True)
        if len(path.split(".")) != 2:
            raise "esi_path not valid: %s" % path
        return path.split(".")

    @classmethod
    def children(cls) -> dict:
        """returns the mapping of children for this class"""
        mappings = cls._eve_universe_meta_attr("children")
        return mappings if mappings else dict()

    @classmethod
    def inline_objects(cls) -> dict:
        """returns a dict of inline objects if any"""
        inline_objects = cls._eve_universe_meta_attr("inline_objects")
        return inline_objects if inline_objects else dict()


class EveUniverseInlineModel(EveUniverseBaseModel):
    """Eve Universe Inline model
    
    Inline models are objects which do not have a dedicated ESI endpoint and are 
    provided through the endpoint of another entity

    This class is also used for static Eve data
    """

    class Meta:
        abstract = True


class EveAncestry(EveUniverseEntityModel):
    """"Ancestry in Eve Online"""

    eve_bloodline = models.ForeignKey("EveBloodline", on_delete=models.CASCADE)
    description = models.TextField()
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    short_description = models.TextField(default="")

    class EveUniverseMeta:
        esi_pk = "id"
        esi_path = "Universe.get_universe_ancestries"
        is_list_endpoint = True
        field_mappings = {"eve_bloodline": "bloodline_id"}


class EveAsteroidBelt(EveUniverseEntityModel):
    """"Asteroid belt in Eve Online"""

    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "asteroid_belt_id"
        esi_path = "Universe.get_universe_asteroid_belts_asteroid_belt_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveBloodline(EveUniverseEntityModel):
    """"Bloodline in Eve Online"""

    charisma = models.PositiveIntegerField()
    corporation_id = models.PositiveIntegerField()
    description = models.TextField()
    intelligence = models.PositiveIntegerField()
    memory = models.PositiveIntegerField()
    perception = models.PositiveIntegerField()
    eve_race = models.ForeignKey(
        "EveRace", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    eve_ship_type = models.ForeignKey("EveType", on_delete=models.CASCADE)
    willpower = models.PositiveIntegerField()

    class EveUniverseMeta:
        esi_pk = "bloodline_id"
        esi_path = "Universe.get_universe_bloodlines"
        is_list_endpoint = True
        field_mappings = {"eve_race": "race_id", "eve_ship_type": "ship_type_id"}


class EveCategory(EveUniverseEntityModel):
    """category in Eve Online"""

    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "category_id"
        esi_path = "Universe.get_universe_categories_category_id"
        children = {"groups": "EveGroup"}


class EveConstellation(EveUniverseEntityModel):
    """constellation in Eve Online"""

    eve_region = models.ForeignKey("EveRegion", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "constellation_id"
        esi_path = "Universe.get_universe_constellations_constellation_id"
        field_mappings = {"eve_region": "region_id"}
        children = {"systems": "EveSolarSystem"}


class EveDogmaAttribute(EveUniverseEntityModel):
    """"Dogma Attribute in Eve Online"""

    default_value = models.FloatField(default=None, null=True)
    description = models.TextField(default="")
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    high_is_good = models.BooleanField(default=None, null=True)
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    published = models.BooleanField(default=None, null=True)
    stackable = models.BooleanField(default=None, null=True)
    eve_unit = models.ForeignKey(
        "EveUnit", on_delete=models.SET_DEFAULT, default=None, null=True
    )

    class EveUniverseMeta:
        esi_pk = "attribute_id"
        esi_path = "Dogma.get_dogma_attributes_attribute_id"
        field_mappings = {"eve_unit": "unit_id"}


class EveDogmaEffect(EveUniverseEntityModel):
    """"Dogma effect in Eve Online"""

    description = models.TextField(default="")
    disallow_auto_repeat = models.BooleanField(default=None, null=True)
    discharge_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="discharge_attribute",
    )
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    duration_attribute = models.ForeignKey(
        "EveDogmaAttribute", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    effect_category = models.PositiveIntegerField(default=None, null=True)
    electronic_chance = models.BooleanField(default=None, null=True)
    falloff_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="falloff_attribute",
    )
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    is_assistance = models.BooleanField(default=None, null=True)
    is_offensive = models.BooleanField(default=None, null=True)
    is_warp_safe = models.BooleanField(default=None, null=True)
    post_expression = models.PositiveIntegerField(default=None, null=True)
    pre_expression = models.PositiveIntegerField(default=None, null=True)
    published = models.BooleanField(default=None, null=True)
    range_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="range_attribute",
    )
    range_chance = models.BooleanField(default=None, null=True)
    tracking_speed_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="tracking_speed_attribute",
    )

    class EveUniverseMeta:
        esi_pk = "effect_id"
        esi_path = "Dogma.get_dogma_effects_effect_id"
        field_mappings = {
            "discharge_attribute": "discharge_attribute_id",
            "duration_attribute": "duration_attribute_id",
            "falloff_attribute": "falloff_attribute_id",
            "range_attribute": "range_attribute_id",
            "tracking_speed_attribute": "tracking_speed_attribute_id",
        }
        inline_objects = {
            "modifiers": "EveDogmaEffectModifier",
        }


class EveDogmaEffectModifier(EveUniverseInlineModel):
    """Modifier for a dogma effect in Eve Online"""

    domain = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    eve_dogma_effect = models.ForeignKey("EveDogmaEffect", on_delete=models.CASCADE)
    func = models.CharField(max_length=NAMES_MAX_LENGTH)
    modified_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modified_attributes",
    )
    modifying_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modifying_attributes",
    )
    modifying_effect = models.ForeignKey(
        "EveDogmaEffect",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="modifying_effects",
    )
    operator = models.PositiveIntegerField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_dogma_effect", "func"], name="functional PK"
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_dogma_effect"
        functional_pk = [
            "eve_dogma_effect",
            "func",
        ]
        field_mappings = {
            "modified_attribute": "modified_attribute_id",
            "modifying_attribute": "modifying_attribute_id",
            "modifying_effect": "effect_id",
        }

    def __repr__(self) -> str:
        return (
            f"EveEffectModifier(eve_type='{self.eve_type}', "
            f"effect_id={self.effect_id})"
        )


class EveFaction(EveUniverseEntityModel):
    """"faction in Eve Online"""

    corporation_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    description = models.TextField()
    is_unique = models.BooleanField()
    militia_corporation_id = models.PositiveIntegerField(
        default=None, null=True, db_index=True
    )
    size_factor = models.FloatField()
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    station_count = models.PositiveIntegerField()
    station_system_count = models.PositiveIntegerField()

    class EveUniverseMeta:
        esi_pk = "faction_id"
        esi_path = "Universe.get_universe_factions"
        is_list_endpoint = True
        field_mappings = {"eve_solar_system": "solar_system_id"}


class EveGroup(EveUniverseEntityModel):
    """group in Eve Online"""

    eve_category = models.ForeignKey("EveCategory", on_delete=models.CASCADE)
    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "group_id"
        esi_path = "Universe.get_universe_groups_group_id"
        field_mappings = {"eve_category": "category_id"}
        children = {"types": "EveType"}


class EveMarketGroup(EveUniverseEntityModel):
    """"Market Group in Eve Online"""

    description = models.TextField()
    parent_market_group = models.ForeignKey(
        "self", on_delete=models.SET_DEFAULT, default=None, null=True
    )

    class EveUniverseMeta:
        esi_pk = "market_group_id"
        esi_path = "Market.get_markets_groups_market_group_id"
        field_mappings = {"parent_market_group": "parent_group_id"}
        children = {"types": "EveType"}


class EveMoon(EveUniverseEntityModel):
    """"moon in Eve Online"""

    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "moon_id"
        esi_path = "Universe.get_universe_moons_moon_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveRace(EveUniverseEntityModel):
    """"faction in Eve Online"""

    alliance_id = models.PositiveIntegerField(db_index=True)
    description = models.TextField()

    class EveUniverseMeta:
        esi_pk = "race_id"
        esi_path = "Universe.get_universe_races"
        is_list_endpoint = True


class EvePlanet(EveUniverseEntityModel):
    """"planet in Eve Online"""

    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)
    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "planet_id"
        esi_path = "Universe.get_universe_planets_planet_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveRegion(EveUniverseEntityModel):
    """region in Eve Online"""

    description = models.TextField(default="")

    class EveUniverseMeta:
        esi_pk = "region_id"
        esi_path = "Universe.get_universe_regions_region_id"
        children = {"constellations": "EveConstellation"}


class EveSolarSystem(EveUniverseEntityModel):
    """solar system in Eve Online"""

    TYPE_HIGHSEC = "highsec"
    TYPE_LOWSEC = "lowsec"
    TYPE_NULLSEC = "nullsec"
    TYPE_W_SPACE = "w-space"
    TYPE_UNKNOWN = "unknown"

    eve_constellation = models.ForeignKey("EveConstellation", on_delete=models.CASCADE)
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    security_status = models.FloatField()

    class EveUniverseMeta:
        esi_pk = "system_id"
        esi_path = "Universe.get_universe_systems_system_id"
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {}

    @property
    def is_high_sec(self):
        return self.security_status > 0.5

    @property
    def is_low_sec(self):
        return 0 < self.security_status <= 0.5

    @property
    def is_null_sec(self):
        return self.security_status <= 0 and not self.is_w_space

    @property
    def is_w_space(self):
        return 31000000 <= self.id < 32000000

    @property
    def space_type(self):
        """returns the space type"""
        if self.is_null_sec:
            return self.TYPE_NULLSEC
        elif self.is_low_sec:
            return self.TYPE_LOWSEC
        elif self.is_high_sec:
            return self.TYPE_HIGHSEC
        elif self.is_w_space:
            return self.TYPE_W_SPACE
        else:
            return self.TYPE_UNKNOWN

    @classmethod
    def children(cls) -> dict:
        children = dict()
        """
        if EVEUNIVERSE_LOAD_ASTEROID_BELTS:
            children["planets"] = "EvePlanet"
        
        if EVEUNIVERSE_LOAD_STARGATES:
            children["stargates"] = "EveStargate"
        
        """

        if EVEUNIVERSE_LOAD_STATIONS:
            children["stations"] = "EveStation"

        return children


class EveStar(EveUniverseEntityModel):
    """"Star in Eve Online"""

    age = models.PositiveIntegerField()
    luminosity = models.FloatField()
    radius = models.PositiveIntegerField()
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)
    spectral_class = models.CharField(max_length=16)
    temperature = models.PositiveIntegerField()
    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "star_id"
        esi_path = "Universe.get_universe_stars_star_id"
        field_mappings = {"eve_solar_system": "solar_system_id", "eve_type": "type_id"}


class EveStargate(EveUniverseEntityModel):
    """"Stargate in Eve Online"""

    destination_eve_stargate = models.ForeignKey(
        "EveStargate",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="destination_eve_stargate_set",
    )
    destination_eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="destination_eve_solar_system_set",
    )
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)
    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "stargate_id"
        esi_path = "Universe.get_universe_stargates_stargate_id"
        field_mappings = {
            "destination_eve_stargate": ("destination", "stargate_id"),
            "destination_eve_solar_system": ("destination", "system_id"),
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveStation(EveUniverseEntityModel):
    """"station in Eve Online"""

    max_dockable_ship_volume = models.FloatField()
    office_rental_cost = models.FloatField()
    owner = models.PositiveIntegerField(default=None, null=True, db_index=True)
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    eve_race = models.ForeignKey(
        "EveRace", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    reprocessing_efficiency = models.FloatField()
    reprocessing_stations_take = models.FloatField()
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)
    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "station_id"
        esi_path = "Universe.get_universe_stations_station_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "eve_race": "race_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveType(EveUniverseEntityModel):
    """Type in Eve Online"""

    capacity = models.FloatField(default=None, null=True)
    eve_group = models.ForeignKey("EveGroup", on_delete=models.CASCADE)
    graphic_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    eve_market_group = models.ForeignKey(
        "EveMarketGroup", on_delete=models.SET_DEFAULT, default=None, null=True
    )
    mass = models.FloatField(default=None, null=True)
    packaged_volume = models.FloatField(default=None, null=True)
    portion_size = models.PositiveIntegerField(default=None, null=True)
    radius = models.FloatField(default=None, null=True)
    published = models.BooleanField()
    volume = models.FloatField(default=None, null=True)

    class EveUniverseMeta:
        esi_pk = "type_id"
        esi_path = "Universe.get_universe_types_type_id"
        field_mappings = {
            "eve_group": "group_id",
            "eve_market_group": "market_group_id",
        }
        inline_objects = {
            "dogma_attributes": "EveTypeDogmaAttribute",
            "dogma_effects": "EveTypeDogmaEffect",
        }

    @classmethod
    def _disabled_fields(cls) -> set:
        if not EVEUNIVERSE_LOAD_MARKET_GROUPS:
            return {"eve_market_group"}
        else:
            return {}

    @classmethod
    def inline_objects(cls) -> dict:
        if EVEUNIVERSE_LOAD_DOGMAS:
            return super().inline_objects()
        else:
            return dict()


class EveTypeDogmaAttribute(EveUniverseInlineModel):
    """Dogma attribute in Eve Online"""

    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_attributes"
    )
    eve_dogma_attribute = models.ForeignKey(
        "EveDogmaAttribute", on_delete=models.CASCADE
    )
    value = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_attribute"], name="functional PK"
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_attribute",
        ]
        field_mappings = {"eve_dogma_attribute": "attribute_id"}

    def __repr__(self) -> str:
        return (
            f"EveTypeDogmaAttributes(eve_type='{self.eve_type}', "
            f"eve_dogma_attribute={self.eve_dogma_attribute}, "
            f"value={self.value})"
        )


class EveTypeDogmaEffect(EveUniverseInlineModel):
    """Dogma effect in Eve Online"""

    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_effects"
    )
    eve_dogma_effect = models.ForeignKey("EveDogmaEffect", on_delete=models.CASCADE)
    is_default = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_effect"], name="functional PK"
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_effect",
        ]
        field_mappings = {"eve_dogma_effect": "effect_id"}

    def __repr__(self) -> str:
        return (
            f"EveTypeDogmaEffect("
            f"eve_type='{self.eve_type}', "
            f"eve_dogma_effect={self.eve_dogma_effect}, "
            f"is_default={self.is_default})"
        )


class EveUnit(EveUniverseEntityModel):
    """Units in Eve Online"""

    display_name = models.CharField(max_length=50, default="")
    description = models.TextField(default="")

    objects = models.Manager()

    class EveUniverseMeta:
        esi_pk = "unit_id"
        esi_path = None
        field_mappings = {
            "unit_id": "id",
            "unit_name": "name",
        }
