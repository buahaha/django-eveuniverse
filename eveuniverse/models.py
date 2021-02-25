from collections import namedtuple
import enum
import inspect
import logging
import math
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

from bravado.exception import HTTPNotFound

from django.db import models
from django.contrib.staticfiles.storage import staticfiles_storage

from bitfield import BitField

from . import __title__
from .app_settings import (
    EVEUNIVERSE_LOAD_DOGMAS,
    EVEUNIVERSE_LOAD_MARKET_GROUPS,
    EVEUNIVERSE_LOAD_ASTEROID_BELTS,
    EVEUNIVERSE_LOAD_GRAPHICS,
    EVEUNIVERSE_LOAD_MOONS,
    EVEUNIVERSE_LOAD_PLANETS,
    EVEUNIVERSE_LOAD_STARGATES,
    EVEUNIVERSE_LOAD_STARS,
    EVEUNIVERSE_LOAD_STATIONS,
    EVEUNIVERSE_LOAD_TYPE_MATERIALS,
    EVEUNIVERSE_USE_EVESKINSERVER,
)
from .constants import EVE_CATEGORY_ID_BLUEPRINT, EVE_CATEGORY_ID_SKIN
from .core import eveimageserver, eveskinserver
from .managers import (
    EveAsteroidBeltManager,
    EveMarketPriceManager,
    EvePlanetManager,
    EveMoonManager,
    EveStargateManager,
    EveStationManager,
    EveEntityManager,
    EveTypeManager,
    EveTypeMaterialManager,
    EveUniverseBaseModelManager,
    EveUniverseEntityModelManager,
)
from .providers import esi
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
        "create_related",
    ],
)


class _SectionBase(str, enum.Enum):
    """Base class for all Sections"""

    @classmethod
    def values(cls) -> list:
        return list(item.value for item in cls)

    def __str__(self) -> str:
        return self.value


class EveUniverseBaseModel(models.Model):
    """Base class for all Eve Universe Models"""

    objects = EveUniverseBaseModelManager()

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        """General purpose __repr__ that works for all model classes"""
        fields = sorted(
            [
                f
                for f in self._meta.get_fields()
                if isinstance(f, models.Field) and f.name != "last_updated"
            ],
            key=lambda x: x.name,
        )
        fields_2 = list()
        for f in fields:
            if f.many_to_one or f.one_to_one:
                name = f"{f.name}_id"
                value = getattr(self, name)
            elif f.many_to_many:
                name = f.name
                value = ", ".join(sorted([str(x) for x in getattr(self, f.name).all()]))
            else:
                name = f.name
                value = getattr(self, f.name)

            if isinstance(value, str):
                if isinstance(f, models.TextField) and len(value) > 32:
                    value = f"{value[:32]}..."
                text = f"{name}='{value}'"
            else:
                text = f"{name}={value}"

            fields_2.append(text)

        return f"{self.__class__.__name__}({', '.join(fields_2)})"

    @classmethod
    def all_models(cls) -> List[Dict[models.Model, int]]:
        """returns a list of all Eve Universe model classes sorted by load order"""
        mappings = list()
        for _, ModelClass in inspect.getmembers(sys.modules[__name__], inspect.isclass):
            if issubclass(
                ModelClass, (EveUniverseEntityModel, EveUniverseInlineModel)
            ) and ModelClass not in (
                cls,
                EveUniverseEntityModel,
                EveUniverseInlineModel,
            ):
                mappings.append(
                    {
                        "model": ModelClass,
                        "load_order": ModelClass._eve_universe_meta_attr(
                            "load_order", is_mandatory=True
                        ),
                    }
                )

        return [y["model"] for y in sorted(mappings, key=lambda x: x["load_order"])]

    @classmethod
    def get_model_class(cls, model_name: str) -> models.Model:
        """returns the model class for the given name"""
        classes = {
            x[0]: x[1]
            for x in inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(x[1], (EveUniverseBaseModel, EveUniverseInlineModel))
        }
        try:
            return classes[model_name]
        except KeyError:
            raise ValueError("Unknown model_name: %s" % model_name)

    @classmethod
    def _esi_mapping(cls, enabled_sections: Set[str] = None) -> dict:
        field_mappings = cls._eve_universe_meta_attr("field_mappings")
        functional_pk = cls._eve_universe_meta_attr("functional_pk")
        parent_fk = cls._eve_universe_meta_attr("parent_fk")
        dont_create_related = cls._eve_universe_meta_attr("dont_create_related")
        disabled_fields = cls._disabled_fields(enabled_sections)
        mapping = dict()
        for field in [
            field
            for field in cls._meta.get_fields()
            if not field.auto_created
            and field.name not in {"last_updated", "enabled_sections"}
            and field.name not in disabled_fields
            and not field.many_to_many
        ]:
            if field_mappings and field.name in field_mappings:
                esi_name = field_mappings[field.name]
            else:
                esi_name = field.name

            if field.primary_key is True:
                is_pk = True
                esi_name = cls._esi_pk()
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

            if dont_create_related and field.name in dont_create_related:
                create_related = False
            else:
                create_related = True

            mapping[field.name] = EsiMapping(
                esi_name=esi_name,
                is_optional=field.has_default(),
                is_pk=is_pk,
                is_fk=is_fk,
                related_model=related_model,
                is_parent_fk=is_parent_fk,
                is_charfield=isinstance(field, (models.CharField, models.TextField)),
                create_related=create_related,
            )

        return mapping

    @classmethod
    def _disabled_fields(cls, enabled_sections: Set[str] = None) -> set:
        """returns name of fields that must not be loaded from ESI"""
        return {}

    @classmethod
    def _eve_universe_meta_attr(
        cls, attr_name: str, is_mandatory: bool = False
    ) -> Optional[Any]:
        """returns value of an attribute from EveUniverseMeta or None"""
        try:
            value = getattr(cls.EveUniverseMeta, attr_name)
        except AttributeError:
            value = None
            if is_mandatory:
                raise ValueError(
                    "Mandatory attribute EveUniverseMeta.%s not defined "
                    "for class %s" % (attr_name, cls.__name__)
                )

        return value


class EveUniverseEntityModel(EveUniverseBaseModel):
    """Base class for Eve Universe Entity models

    Entity models are normal Eve entities that have a dedicated ESI endpoint
    """

    class Section(_SectionBase):
        pass

    # sections
    LOAD_DOGMAS = "dogmas"
    # TODO: Implement other sections

    # icons
    DEFAULT_ICON_SIZE = 64

    id = models.PositiveIntegerField(primary_key=True, help_text="Eve Online ID")
    name = models.CharField(
        max_length=NAMES_MAX_LENGTH,
        default="",
        db_index=True,
        help_text="Eve Online name",
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When this object was last updated from ESI",
        db_index=True,
    )

    objects = EveUniverseEntityModelManager()

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name

    @classmethod
    def _enabled_sections_union(cls, enabled_sections: Iterable[str] = None) -> set:
        """returns union of global and given enabled sections.
        Needs to be overloaded by sub class using sections
        """
        enabled_sections = set(enabled_sections) if enabled_sections else set()
        if EVEUNIVERSE_LOAD_ASTEROID_BELTS:
            enabled_sections.add(EvePlanet.Section.ASTEROID_BELTS)
        if EVEUNIVERSE_LOAD_DOGMAS:
            enabled_sections.add(EveType.Section.DOGMAS)
        if EVEUNIVERSE_LOAD_GRAPHICS:
            enabled_sections.add(EveType.Section.GRAPHICS)
        if EVEUNIVERSE_LOAD_MARKET_GROUPS:
            enabled_sections.add(EveType.Section.MARKET_GROUPS)
        if EVEUNIVERSE_LOAD_MOONS:
            enabled_sections.add(EvePlanet.Section.MOONS)
        if EVEUNIVERSE_LOAD_PLANETS:
            enabled_sections.add(EveSolarSystem.Section.PLANETS)
        if EVEUNIVERSE_LOAD_STARGATES:
            enabled_sections.add(EveSolarSystem.Section.STARGATES)
        if EVEUNIVERSE_LOAD_STARS:
            enabled_sections.add(EveSolarSystem.Section.STARS)
        if EVEUNIVERSE_LOAD_STATIONS:
            enabled_sections.add(EveSolarSystem.Section.STATIONS)
        if EVEUNIVERSE_LOAD_TYPE_MATERIALS:
            enabled_sections.add(EveType.Section.TYPE_MATERIALS)
        return enabled_sections

    @classmethod
    def eve_entity_category(cls) -> str:
        """returns the EveEntity category of this model if one exists
        else and empty string
        """
        return ""

    @classmethod
    def _esi_pk(cls) -> str:
        """returns the name of the pk column on ESI that must exist"""
        return cls._eve_universe_meta_attr("esi_pk", is_mandatory=True)

    @classmethod
    def _has_esi_path_list(cls) -> str:
        return bool(cls._eve_universe_meta_attr("esi_path_list"))

    @classmethod
    def _esi_path_list(cls) -> str:
        return cls._esi_path("list")

    @classmethod
    def _esi_path_object(cls) -> str:
        return cls._esi_path("object")

    @classmethod
    def _esi_path(cls, variant: str) -> Tuple[str, str]:
        attr_name = f"esi_path_{str(variant)}"
        path = cls._eve_universe_meta_attr(attr_name, is_mandatory=True)
        if len(path.split(".")) != 2:
            raise ValueError(f"{attr_name} not valid")
        return path.split(".")

    @classmethod
    def _children(cls, enabled_sections: Iterable[str] = None) -> dict:
        """returns the mapping of children for this class"""
        mappings = cls._eve_universe_meta_attr("children")
        return mappings if mappings else dict()

    @classmethod
    def _inline_objects(cls, enabled_sections: Set[str] = None) -> dict:
        """returns a dict of inline objects if any"""
        inline_objects = cls._eve_universe_meta_attr("inline_objects")
        return inline_objects if inline_objects else dict()

    @classmethod
    def _is_list_only_endpoint(cls) -> bool:
        esi_path_list = cls._eve_universe_meta_attr("esi_path_list")
        esi_path_object = cls._eve_universe_meta_attr("esi_path_object")
        return esi_path_list and esi_path_object and esi_path_list == esi_path_object


class EveUniverseInlineModel(EveUniverseBaseModel):
    """Base class for Eve Universe Inline models

    Inline models are objects which do not have a dedicated ESI endpoint and are
    provided through the endpoint of another entity

    This class is also used for static Eve data
    """

    class Meta:
        abstract = True


class EveEntity(EveUniverseEntityModel):
    """An Eve object from one of the categories supported by ESI's
    `/universe/names/` endpoint:

    alliance, character, constellation, faction, type, region, solar system, station


    This is a special model model dedicated to quick resolution of Eve IDs to names and their categories, e.g. for characters. See also manager methods.
    """

    # NPC IDs
    NPC_CORPORATION_ID_BEGIN = 1_000_000
    NPC_CORPORATION_ID_END = 2_000_000
    NPC_CHARACTER_ID_BEGIN = 3_000_000
    NPC_CHARACTER_ID_END = 4_000_000

    # categories
    CATEGORY_ALLIANCE = "alliance"
    CATEGORY_CHARACTER = "character"
    CATEGORY_CONSTELLATION = "constellation"
    CATEGORY_CORPORATION = "corporation"
    CATEGORY_FACTION = "faction"
    CATEGORY_INVENTORY_TYPE = "inventory_type"
    CATEGORY_REGION = "region"
    CATEGORY_SOLAR_SYSTEM = "solar_system"
    CATEGORY_STATION = "station"

    CATEGORY_CHOICES = (
        (CATEGORY_ALLIANCE, "alliance"),
        (CATEGORY_CHARACTER, "character"),
        (CATEGORY_CONSTELLATION, "constellation"),
        (CATEGORY_CORPORATION, "corporation"),
        (CATEGORY_FACTION, "faction"),
        (CATEGORY_INVENTORY_TYPE, "inventory_type"),
        (CATEGORY_REGION, "region"),
        (CATEGORY_SOLAR_SYSTEM, "solar_system"),
        (CATEGORY_STATION, "station"),
    )

    category = models.CharField(
        max_length=16, choices=CATEGORY_CHOICES, default=None, null=True
    )

    objects = EveEntityManager()

    class EveUniverseMeta:
        esi_pk = "ids"
        esi_path_object = "Universe.post_universe_names"
        load_order = 110

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._CATEGORIES = {x[0] for x in self.CATEGORY_CHOICES}

    def __str__(self) -> str:
        if self.name:
            return self.name
        else:
            return f"ID:{self.id}"

    @property
    def is_alliance(self) -> bool:
        """returns True if entity is an alliance, else False"""
        return self.is_category(self.CATEGORY_ALLIANCE)

    @property
    def is_character(self) -> bool:
        """returns True if entity is a character, else False"""
        return self.is_category(self.CATEGORY_CHARACTER)

    @property
    def is_constellation(self) -> bool:
        """returns True if entity is a constellation, else False"""
        return self.is_category(self.CATEGORY_CONSTELLATION)

    @property
    def is_corporation(self) -> bool:
        """returns True if entity is a corporation, else False"""
        return self.is_category(self.CATEGORY_CORPORATION)

    @property
    def is_faction(self) -> bool:
        """returns True if entity is a faction, else False"""
        return self.is_category(self.CATEGORY_FACTION)

    @property
    def is_type(self) -> bool:
        """returns True if entity is an inventory type, else False"""
        return self.is_category(self.CATEGORY_INVENTORY_TYPE)

    @property
    def is_region(self) -> bool:
        """returns True if entity is a region, else False"""
        return self.is_category(self.CATEGORY_REGION)

    @property
    def is_solar_system(self) -> bool:
        """returns True if entity is a solar system, else False"""
        return self.is_category(self.CATEGORY_SOLAR_SYSTEM)

    @property
    def is_station(self) -> bool:
        """returns True if entity is a station, else False"""
        return self.is_category(self.CATEGORY_STATION)

    @property
    def is_npc(self) -> bool:
        """returns True if this entity is an NPC character or NPC corporation,
        else False
        """
        if (
            self.is_corporation
            and self.NPC_CORPORATION_ID_BEGIN <= self.id < self.NPC_CORPORATION_ID_END
        ):
            return True

        if (
            self.is_character
            and self.NPC_CHARACTER_ID_BEGIN <= self.id < self.NPC_CHARACTER_ID_END
        ):
            return True

        return False

    def is_category(self, category: str) -> bool:
        """returns True if this entity has the given category, else False"""
        return category in self._CATEGORIES and self.category == category

    def update_from_esi(self) -> "EveEntity":
        """Update the current object from ESI

        Returns:
            itself after update
        """
        obj, _ = EveEntity.objects.update_or_create_esi(id=self.id)
        return obj

    def icon_url(self, size: int = EveUniverseEntityModel.DEFAULT_ICON_SIZE) -> str:
        """Create image URL for related EVE icon

        Args:
            size: size of image file in pixels, allowed values: 32, 64, 128, 256, 512

        Return:
            strings with image URL
        """
        map_category_2_other = {
            self.CATEGORY_ALLIANCE: "alliance_logo_url",
            self.CATEGORY_CHARACTER: "character_portrait_url",
            self.CATEGORY_CORPORATION: "corporation_logo_url",
            self.CATEGORY_FACTION: "faction_logo_url",
            self.CATEGORY_INVENTORY_TYPE: "type_icon_url",
        }
        if self.category not in map_category_2_other:
            return ""
        else:
            func = map_category_2_other[self.category]
            return getattr(eveimageserver, func)(self.id, size=size)


class EveAncestry(EveUniverseEntityModel):
    """An ancestry in Eve Online"""

    eve_bloodline = models.ForeignKey(
        "EveBloodline", on_delete=models.CASCADE, related_name="eve_bloodlines"
    )
    description = models.TextField()
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    short_description = models.TextField(default="")

    class EveUniverseMeta:
        esi_pk = "id"
        esi_path_list = "Universe.get_universe_ancestries"
        esi_path_object = "Universe.get_universe_ancestries"
        field_mappings = {"eve_bloodline": "bloodline_id"}
        load_order = 180


class EveAsteroidBelt(EveUniverseEntityModel):
    """An asteroid belt in Eve Online"""

    eve_planet = models.ForeignKey(
        "EvePlanet", on_delete=models.CASCADE, related_name="eve_asteroid_belts"
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

    objects = EveAsteroidBeltManager()

    class EveUniverseMeta:
        esi_pk = "asteroid_belt_id"
        esi_path_object = "Universe.get_universe_asteroid_belts_asteroid_belt_id"
        field_mappings = {
            "eve_planet": "planet_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        load_order = 200


class EveBloodline(EveUniverseEntityModel):
    """A bloodline in Eve Online"""

    eve_race = models.ForeignKey(
        "EveRace",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_bloodlines",
    )
    eve_ship_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_bloodlines"
    )
    charisma = models.PositiveIntegerField()
    corporation_id = models.PositiveIntegerField()
    description = models.TextField()
    intelligence = models.PositiveIntegerField()
    memory = models.PositiveIntegerField()
    perception = models.PositiveIntegerField()
    willpower = models.PositiveIntegerField()

    class EveUniverseMeta:
        esi_pk = "bloodline_id"
        esi_path_list = "Universe.get_universe_bloodlines"
        esi_path_object = "Universe.get_universe_bloodlines"
        field_mappings = {"eve_race": "race_id", "eve_ship_type": "ship_type_id"}
        load_order = 170


class EveCategory(EveUniverseEntityModel):
    """An inventory category in Eve Online"""

    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "category_id"
        esi_path_list = "Universe.get_universe_categories"
        esi_path_object = "Universe.get_universe_categories_category_id"
        children = {"groups": "EveGroup"}
        load_order = 130


class EveConstellation(EveUniverseEntityModel):
    """A star constellation in Eve Online"""

    eve_region = models.ForeignKey(
        "EveRegion", on_delete=models.CASCADE, related_name="eve_constellations"
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

    class EveUniverseMeta:
        esi_pk = "constellation_id"
        esi_path_list = "Universe.get_universe_constellations"
        esi_path_object = "Universe.get_universe_constellations_constellation_id"
        field_mappings = {
            "eve_region": "region_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {"systems": "EveSolarSystem"}
        load_order = 192

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_CONSTELLATION


class EveDogmaAttribute(EveUniverseEntityModel):
    """A dogma attribute in Eve Online"""

    eve_unit = models.ForeignKey(
        "EveUnit",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_units",
    )
    default_value = models.FloatField(default=None, null=True)
    description = models.TextField(default="")
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    high_is_good = models.BooleanField(default=None, null=True)
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    published = models.BooleanField(default=None, null=True)
    stackable = models.BooleanField(default=None, null=True)

    class EveUniverseMeta:
        esi_pk = "attribute_id"
        esi_path_list = "Dogma.get_dogma_attributes"
        esi_path_object = "Dogma.get_dogma_attributes_attribute_id"
        field_mappings = {"eve_unit": "unit_id"}
        load_order = 140


class EveDogmaEffect(EveUniverseEntityModel):
    """A dogma effect in Eve Online"""

    # we need to redefine the name field, because effect names can be very long
    name = models.CharField(
        max_length=400,
        default="",
        db_index=True,
        help_text="Eve Online name",
    )

    description = models.TextField(default="")
    disallow_auto_repeat = models.BooleanField(default=None, null=True)
    discharge_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="discharge_attribute_effects",
    )
    display_name = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    duration_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="duration_attribute_effects",
    )
    effect_category = models.PositiveIntegerField(default=None, null=True)
    electronic_chance = models.BooleanField(default=None, null=True)
    falloff_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="falloff_attribute_effects",
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
        related_name="range_attribute_effects",
    )
    range_chance = models.BooleanField(default=None, null=True)
    tracking_speed_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="tracking_speed_attribute_effects",
    )

    class EveUniverseMeta:
        esi_pk = "effect_id"
        esi_path_list = "Dogma.get_dogma_effects"
        esi_path_object = "Dogma.get_dogma_effects_effect_id"
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
        load_order = 142


class EveDogmaEffectModifier(EveUniverseInlineModel):
    """A modifier for a dogma effect in Eve Online"""

    domain = models.CharField(max_length=NAMES_MAX_LENGTH, default="")
    eve_dogma_effect = models.ForeignKey(
        "EveDogmaEffect", on_delete=models.CASCADE, related_name="modifiers"
    )
    func = models.CharField(max_length=NAMES_MAX_LENGTH)
    modified_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modified_attribute_modifiers",
    )
    modifying_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="modifying_attribute_modifiers",
    )
    modifying_effect = models.ForeignKey(
        "EveDogmaEffect",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="modifying_effect_modifiers",
    )
    operator = models.PositiveIntegerField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_dogma_effect", "func"],
                name="fpk_evedogmaeffectmodifier",
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
        load_order = 144


class EveFaction(EveUniverseEntityModel):
    """A faction in Eve Online"""

    corporation_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    description = models.TextField()
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_factions",
    )
    is_unique = models.BooleanField()
    militia_corporation_id = models.PositiveIntegerField(
        default=None, null=True, db_index=True
    )
    size_factor = models.FloatField()
    station_count = models.PositiveIntegerField()
    station_system_count = models.PositiveIntegerField()

    class EveUniverseMeta:
        esi_pk = "faction_id"
        esi_path_list = "Universe.get_universe_factions"
        esi_path_object = "Universe.get_universe_factions"
        field_mappings = {"eve_solar_system": "solar_system_id"}
        load_order = 210

    def logo_url(self, size=EveUniverseEntityModel.DEFAULT_ICON_SIZE) -> str:
        """returns an image URL for this faction

        Args:
            size: optional size of the image
        """
        return eveimageserver.faction_logo_url(self.id, size=size)

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_FACTION


class EveGraphic(EveUniverseEntityModel):
    """A graphic in Eve Online"""

    FILENAME_MAX_CHARS = 255

    collision_file = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    graphic_file = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    icon_folder = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_dna = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_fation_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_hull_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")
    sof_race_name = models.CharField(max_length=FILENAME_MAX_CHARS, default="")

    class EveUniverseMeta:
        esi_pk = "graphic_id"
        esi_path_list = "Universe.get_universe_graphics"
        esi_path_object = "Universe.get_universe_graphics_graphic_id"
        load_order = 120


class EveGroup(EveUniverseEntityModel):
    """An inventory group in Eve Online"""

    eve_category = models.ForeignKey(
        "EveCategory", on_delete=models.CASCADE, related_name="eve_groups"
    )
    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "group_id"
        esi_path_list = "Universe.get_universe_groups"
        esi_path_object = "Universe.get_universe_groups_group_id"
        field_mappings = {"eve_category": "category_id"}
        children = {"types": "EveType"}
        load_order = 132


class EveMarketGroup(EveUniverseEntityModel):
    """A market group in Eve Online"""

    description = models.TextField()
    parent_market_group = models.ForeignKey(
        "self",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="market_group_children",
    )

    class EveUniverseMeta:
        esi_pk = "market_group_id"
        esi_path_list = "Market.get_markets_groups"
        esi_path_object = "Market.get_markets_groups_market_group_id"
        field_mappings = {"parent_market_group": "parent_group_id"}
        children = {"types": "EveType"}
        load_order = 230


class EveMarketPrice(models.Model):
    """A market price of an Eve Online type"""

    DEFAULT_MINUTES_UNTIL_STALE = 60

    eve_type = models.OneToOneField(
        "EveType",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="market_price",
    )
    adjusted_price = models.FloatField(default=None, null=True)
    average_price = models.FloatField(default=None, null=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    objects = EveMarketPriceManager()

    def __str__(self) -> str:
        return f"{self.eve_type}: {self.average_price}"

    def __repr__(self) -> str:
        return "{}(eve_type='{}', adjusted_price={}, average_price={}, updated_at={})".format(
            type(self).__name__,
            self.eve_type,
            self.adjusted_price,
            self.average_price,
            self.updated_at.isoformat(),
        )


class EveMoon(EveUniverseEntityModel):
    """A moon in Eve Online"""

    eve_planet = models.ForeignKey(
        "EvePlanet", on_delete=models.CASCADE, related_name="eve_moons"
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

    objects = EveMoonManager()

    class EveUniverseMeta:
        esi_pk = "moon_id"
        esi_path_object = "Universe.get_universe_moons_moon_id"
        field_mappings = {
            "eve_planet": "planet_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        load_order = 220


class EvePlanet(EveUniverseEntityModel):
    """A planet in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        ASTEROID_BELTS = "asteroid_belts"  #:
        MOONS = "moons"  #:

    eve_solar_system = models.ForeignKey(
        "EveSolarSystem", on_delete=models.CASCADE, related_name="eve_planets"
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_planets"
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
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )

    objects = EvePlanetManager()

    class EveUniverseMeta:
        esi_pk = "planet_id"
        esi_path_object = "Universe.get_universe_planets_planet_id"
        field_mappings = {
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {"moons": "EveMoon", "asteroid_belts": "EveAsteroidBelt"}
        load_order = 205

    @classmethod
    def _children(cls, enabled_sections: Iterable[str] = None) -> dict:
        enabled_sections = cls._enabled_sections_union(enabled_sections)
        children = dict()
        if cls.Section.ASTEROID_BELTS in enabled_sections:
            children["asteroid_belts"] = "EveAsteroidBelt"
        if cls.Section.MOONS in enabled_sections:
            children["moons"] = "EveMoon"
        return children


class EveRace(EveUniverseEntityModel):
    """A race in Eve Online"""

    alliance_id = models.PositiveIntegerField(db_index=True)
    description = models.TextField()

    class EveUniverseMeta:
        esi_pk = "race_id"
        esi_path_list = "Universe.get_universe_races"
        esi_path_object = "Universe.get_universe_races"
        load_order = 150


class EveRegion(EveUniverseEntityModel):
    """A star region in Eve Online"""

    description = models.TextField(default="")

    class EveUniverseMeta:
        esi_pk = "region_id"
        esi_path_list = "Universe.get_universe_regions"
        esi_path_object = "Universe.get_universe_regions_region_id"
        children = {"constellations": "EveConstellation"}
        load_order = 190

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_REGION


class EveSolarSystem(EveUniverseEntityModel):
    """A solar system in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        PLANETS = "planets"  #:
        STARGATES = "stargates"  #:
        STARS = "stars"  #
        STATIONS = "stations"  #:

    eve_constellation = models.ForeignKey(
        "EveConstellation", on_delete=models.CASCADE, related_name="eve_solarsystems"
    )
    eve_star = models.OneToOneField(
        "EveStar",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_solarsystem",
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
    security_status = models.FloatField()
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )

    class EveUniverseMeta:
        esi_pk = "system_id"
        esi_path_list = "Universe.get_universe_systems"
        esi_path_object = "Universe.get_universe_systems_system_id"
        field_mappings = {
            "eve_constellation": "constellation_id",
            "eve_star": "star_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {}
        load_order = 194

    @property
    def is_high_sec(self) -> bool:
        """returns True if this solar system is in high sec, else False"""
        return round(self.security_status, 1) >= 0.5

    @property
    def is_low_sec(self) -> bool:
        """returns True if this solar system is in low sec, else False"""
        return 0 < round(self.security_status, 1) < 0.5

    @property
    def is_null_sec(self) -> bool:
        """returns True if this solar system is in null sec, else False"""
        return round(self.security_status, 1) <= 0 and not self.is_w_space

    @property
    def is_w_space(self) -> bool:
        """returns True if this solar system is in wormhole space, else False"""
        return 31000000 <= self.id < 32000000

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_SOLAR_SYSTEM

    def distance_to(self, destination: "EveSolarSystem") -> Optional[float]:
        """Calculates the distance in meters between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            Distance in meters or None if one of the systems is in WH space
        """
        if self.is_w_space or destination.is_w_space:
            return None
        else:
            return math.sqrt(
                (destination.position_x - self.position_x) ** 2
                + (destination.position_y - self.position_y) ** 2
                + (destination.position_z - self.position_z) ** 2
            )

    def route_to(
        self, destination: "EveSolarSystem"
    ) -> Optional[List["EveSolarSystem"]]:
        """Calculates the shortest route between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            List of solar system objects incl. origin and destination or None if no route can be found (e.g. if one system is in WH space)
        """
        path_ids = self._calc_route_esi(self.id, destination.id)
        if path_ids is not None:
            return [
                EveSolarSystem.objects.get_or_create_esi(id=solar_system_id)
                for solar_system_id in path_ids
            ]
        else:
            return None

    def jumps_to(self, destination: "EveSolarSystem") -> Optional[int]:
        """Calculates the shortest route between the current and the given solar system

        Args:
            destination: Other solar system to use in calculation

        Returns:
            Number of total jumps or None if no route can be found (e.g. if one system is in WH space)
        """
        path_ids = self._calc_route_esi(self.id, destination.id)
        return len(path_ids) - 1 if path_ids is not None else None

    @staticmethod
    def _calc_route_esi(origin_id: int, destination_id: int) -> Optional[List[int]]:
        """returns the shortest route between two given solar systems.

        Route is calculated by ESI

        Args:
            destination_id: ID of the other solar system to use in calculation

        Returns:
            List of solar system IDs incl. origin and destination or None if no route can be found (e.g. if one system is in WH space)
        """

        try:
            return esi.client.Routes.get_route_origin_destination(
                origin=origin_id, destination=destination_id
            ).results()
        except HTTPNotFound:
            return None

    @classmethod
    def _children(cls, enabled_sections: Iterable[str] = None) -> dict:
        enabled_sections = cls._enabled_sections_union(enabled_sections)
        children = dict()
        if cls.Section.PLANETS in enabled_sections:
            children["planets"] = "EvePlanet"
        if cls.Section.STARGATES in enabled_sections:
            children["stargates"] = "EveStargate"
        if cls.Section.STATIONS in enabled_sections:
            children["stations"] = "EveStation"
        return children

    @classmethod
    def _disabled_fields(cls, enabled_sections: Set[str] = None) -> set:
        enabled_sections = cls._enabled_sections_union(enabled_sections)
        if cls.Section.STARS not in enabled_sections:
            return {"eve_star"}
        return {}

    @classmethod
    def _inline_objects(cls, enabled_sections: Set[str] = None) -> dict:
        if enabled_sections and cls.Section.PLANETS in enabled_sections:
            return super()._inline_objects()
        else:
            return dict()


class EveStar(EveUniverseEntityModel):
    """A star in Eve Online"""

    age = models.BigIntegerField()
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_stars"
    )
    luminosity = models.FloatField()
    radius = models.PositiveIntegerField()
    spectral_class = models.CharField(max_length=16)
    temperature = models.PositiveIntegerField()

    class EveUniverseMeta:
        esi_pk = "star_id"
        esi_path_object = "Universe.get_universe_stars_star_id"
        field_mappings = {"eve_type": "type_id"}
        load_order = 222


class EveStargate(EveUniverseEntityModel):
    """A stargate in Eve Online"""

    destination_eve_stargate = models.OneToOneField(
        "EveStargate", on_delete=models.SET_DEFAULT, null=True, default=None, blank=True
    )
    destination_eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.SET_DEFAULT,
        null=True,
        default=None,
        blank=True,
        related_name="destination_eve_stargates",
    )
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem", on_delete=models.CASCADE, related_name="eve_stargates"
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="eve_stargates"
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

    objects = EveStargateManager()

    class EveUniverseMeta:
        esi_pk = "stargate_id"
        esi_path_object = "Universe.get_universe_stargates_stargate_id"
        field_mappings = {
            "destination_eve_stargate": ("destination", "stargate_id"),
            "destination_eve_solar_system": ("destination", "system_id"),
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        dont_create_related = {
            "destination_eve_stargate",
            "destination_eve_solar_system",
        }
        load_order = 224


class EveStation(EveUniverseEntityModel):
    """A space station in Eve Online"""

    eve_race = models.ForeignKey(
        "EveRace",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_stations",
    )
    eve_solar_system = models.ForeignKey(
        "EveSolarSystem",
        on_delete=models.CASCADE,
        related_name="eve_stations",
    )
    eve_type = models.ForeignKey(
        "EveType",
        on_delete=models.CASCADE,
        related_name="eve_stations",
    )
    max_dockable_ship_volume = models.FloatField()
    office_rental_cost = models.FloatField()
    owner_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    position_x = models.FloatField(
        null=True, default=None, blank=True, help_text="x position in the solar system"
    )
    position_y = models.FloatField(
        null=True, default=None, blank=True, help_text="y position in the solar system"
    )
    position_z = models.FloatField(
        null=True, default=None, blank=True, help_text="z position in the solar system"
    )
    reprocessing_efficiency = models.FloatField()
    reprocessing_stations_take = models.FloatField()
    services = models.ManyToManyField("EveStationService")

    objects = EveStationManager()

    class EveUniverseMeta:
        esi_pk = "station_id"
        esi_path_object = "Universe.get_universe_stations_station_id"
        field_mappings = {
            "eve_race": "race_id",
            "eve_solar_system": "system_id",
            "eve_type": "type_id",
            "owner_id": "owner",
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        inline_objects = {"services": "EveStationService"}
        load_order = 207

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_STATION


class EveStationService(models.Model):
    """A service in a space station"""

    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class EveType(EveUniverseEntityModel):
    """An inventory type in Eve Online"""

    class Section(_SectionBase):
        """Sections that can be optionally loaded with each instance"""

        DOGMAS = "dogmas"  #:
        GRAPHICS = "graphics"  #:
        MARKET_GROUPS = "market_groups"  #
        TYPE_MATERIALS = "type_materials"  #:

    capacity = models.FloatField(default=None, null=True)
    eve_group = models.ForeignKey(
        "EveGroup",
        on_delete=models.CASCADE,
        related_name="eve_types",
    )
    eve_graphic = models.ForeignKey(
        "EveGraphic",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_types",
    )
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    eve_market_group = models.ForeignKey(
        "EveMarketGroup",
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        related_name="eve_types",
    )
    mass = models.FloatField(default=None, null=True)
    packaged_volume = models.FloatField(default=None, null=True)
    portion_size = models.PositiveIntegerField(default=None, null=True)
    radius = models.FloatField(default=None, null=True)
    published = models.BooleanField()  # TODO: Add index
    volume = models.FloatField(default=None, null=True)
    enabled_sections = BitField(
        flags=tuple(Section.values()),
        help_text=(
            "Flags for loadable sections. True if instance was loaded with section."
        ),  # no index, because MySQL does not support it for bitwise operations
    )

    objects = EveTypeManager()

    class EveUniverseMeta:
        esi_pk = "type_id"
        esi_path_list = "Universe.get_universe_types"
        esi_path_object = "Universe.get_universe_types_type_id"
        field_mappings = {
            "eve_graphic": "graphic_id",
            "eve_group": "group_id",
            "eve_market_group": "market_group_id",
        }
        inline_objects = {
            "dogma_attributes": "EveTypeDogmaAttribute",
            "dogma_effects": "EveTypeDogmaEffect",
        }
        load_order = 134

    class IconVariant(enum.Enum):
        """Variant of icon to produce with `icon_url()`"""

        REGULAR = enum.auto()
        """anything, except blueprint or skin"""

        BPO = enum.auto()
        """blueprint original"""

        BPC = enum.auto()
        """blueprint copy"""

        SKIN = enum.auto()
        """SKIN"""

    def icon_url(
        self,
        size: int = EveUniverseEntityModel.DEFAULT_ICON_SIZE,
        variant: IconVariant = None,
        category_id: int = None,
        is_blueprint: bool = None,
    ) -> str:
        """returns an image URL to this type as icon. Also works for blueprints and SKINs.

        Will try to auto-detect the variant based on the types's category,
        unless `variant` or `category_id` is specified.

        Args:
            variant: icon variant to use
            category_id: category ID of this type
            is_blueprint: DEPRECATED - type is assumed to be a blueprint
        """
        # if is_blueprint is not None:
        #    warnings.warn("is_blueprint in EveType.icon_url() is deprecated")

        if is_blueprint:
            variant = self.IconVariant.BPO

        if not variant:
            if not category_id:
                category_id = self.eve_group.eve_category_id

            if category_id == EVE_CATEGORY_ID_BLUEPRINT:
                variant = self.IconVariant.BPO

            elif category_id == EVE_CATEGORY_ID_SKIN:
                variant = self.IconVariant.SKIN

        if variant is self.IconVariant.BPO:
            return eveimageserver.type_bp_url(self.id, size=size)

        if variant is self.IconVariant.BPC:
            return eveimageserver.type_bpc_url(self.id, size=size)

        if variant is self.IconVariant.SKIN:
            size = EveUniverseEntityModel.DEFAULT_ICON_SIZE if not size else size
            if EVEUNIVERSE_USE_EVESKINSERVER:
                return eveskinserver.type_icon_url(self.id, size=size)

            if size < 32 or size > 128 or (size & (size - 1) != 0):
                raise ValueError("Invalid size: {}".format(size))
            filename = f"eveuniverse/skin_generic_{size}.png"
            return staticfiles_storage.url(filename)

        return eveimageserver.type_icon_url(self.id, size=size)

    def render_url(self, size=EveUniverseEntityModel.DEFAULT_ICON_SIZE) -> str:
        """return an image URL to this type as render"""
        return eveimageserver.type_render_url(self.id, size=size)

    @classmethod
    def _disabled_fields(cls, enabled_sections: Set[str] = None) -> set:
        enabled_sections = cls._enabled_sections_union(enabled_sections)
        disabled_fields = set()
        if cls.Section.GRAPHICS not in enabled_sections:
            disabled_fields.add("eve_graphic")
        if cls.Section.MARKET_GROUPS not in enabled_sections:
            disabled_fields.add("eve_market_group")
        return disabled_fields

    @classmethod
    def _inline_objects(cls, enabled_sections: Set[str] = None) -> dict:
        if enabled_sections and cls.Section.DOGMAS in enabled_sections:
            return super()._inline_objects()
        else:
            return dict()

    @classmethod
    def eve_entity_category(cls) -> str:
        return EveEntity.CATEGORY_INVENTORY_TYPE


class EveTypeDogmaAttribute(EveUniverseInlineModel):
    """A dogma attribute of on inventory type in Eve Online"""

    eve_dogma_attribute = models.ForeignKey(
        "EveDogmaAttribute",
        on_delete=models.CASCADE,
        related_name="eve_type_dogma_attributes",
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_attributes"
    )
    value = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_attribute"],
                name="fpk_evetypedogmaattribute",
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_attribute",
        ]
        field_mappings = {"eve_dogma_attribute": "attribute_id"}
        load_order = 148


class EveTypeDogmaEffect(EveUniverseInlineModel):
    """A dogma effect of on inventory type in Eve Online"""

    eve_dogma_effect = models.ForeignKey(
        "EveDogmaEffect",
        on_delete=models.CASCADE,
        related_name="eve_type_dogma_effects",
    )
    eve_type = models.ForeignKey(
        "EveType", on_delete=models.CASCADE, related_name="dogma_effects"
    )
    is_default = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "eve_dogma_effect"],
                name="fpk_evetypedogmaeffect",
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        functional_pk = [
            "eve_type",
            "eve_dogma_effect",
        ]
        field_mappings = {"eve_dogma_effect": "effect_id"}
        load_order = 146


class EveUnit(EveUniverseEntityModel):
    """A unit in Eve Online"""

    display_name = models.CharField(max_length=50, default="")
    description = models.TextField(default="")

    objects = models.Manager()

    class EveUniverseMeta:
        esi_pk = "unit_id"
        esi_path_object = None
        field_mappings = {
            "unit_id": "id",
            "unit_name": "name",
        }
        load_order = 100


#######################
# SDE models


class EveTypeMaterial(EveUniverseBaseModel):
    """Material type for an Eve online type"""

    eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, related_name="materials"
    )
    material_eve_type = models.ForeignKey(
        EveType, on_delete=models.CASCADE, related_name="material_types"
    )
    quantity = models.PositiveIntegerField()

    objects = EveTypeMaterialManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "material_eve_type"],
                name="fpk_evetypematerial",
            )
        ]

    def __str__(self) -> str:
        return f"{self.eve_type}-{self.material_eve_type}"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"eve_type={repr(self.eve_type)}, "
            f"material_eve_type={repr(self.material_eve_type)}, "
            f"quantity={self.quantity}"
            ")"
        )
