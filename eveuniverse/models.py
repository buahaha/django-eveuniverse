from django.db import models
from django.utils.timezone import now

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .managers import EveUniverseModelManager, EveUniverseListManager
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverseBaseModel(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def esi_pk(cls) -> str:
        """returns the name of the pk column on ESI that must exist"""
        return cls._eve_universe_meta_attr("esi_pk", is_mandatory=True)

    @classmethod
    def parent_fk(cls) -> str:
        return cls._eve_universe_meta_attr("parent_fk", is_mandatory=True)

    @classmethod
    def map_esi_fields_to_model(cls, eve_data_obj: dict) -> dict:
        """maps ESi fields to model fields incl. translations if any
        returns the result as defaults dict
        """
        fk_mappings = cls._fk_mappings()
        field_mappings = cls._field_mappings()
        defaults = {"last_updated": now()}
        for key in cls._field_names_not_pk():
            if key in fk_mappings:
                esi_key, ParentClass = fk_mappings[key]
                try:
                    value = ParentClass.objects.get(id=eve_data_obj[esi_key])
                except ParentClass.DoesNotExist:
                    if hasattr(ParentClass.objects, "update_or_create_esi"):
                        value, _ = ParentClass.objects.update_or_create_esi(
                            eve_data_obj[esi_key]
                        )
                    else:
                        value = None
            else:
                if key in field_mappings:
                    mapping = field_mappings[key]
                    if len(mapping) != 2:
                        raise ValueError(
                            "Currently only supports mapping to 1-level " "nested dicts"
                        )
                    value = eve_data_obj[mapping[0]][mapping[1]]
                else:
                    value = eve_data_obj[key]

            defaults[key] = value

        return defaults

    @classmethod
    def _field_mappings(cls) -> dict:
        """returns the mappings for model fields vs. esi fields"""
        mappings = cls._eve_universe_meta_attr("field_mappings")
        return mappings if mappings else dict()

    @classmethod
    def _fk_mappings(cls) -> dict:
        """returns the foreign key mappings for this class
        
        'model field name': ('Foreign Key name on ESI', 'related model class')
        """

        def convert_to_esi_name(name: str, extra_fk_mappings: dict) -> str:
            if name in extra_fk_mappings:
                esi_name = extra_fk_mappings[name]
            else:
                esi_name = name.replace("eve_", "") + "_id"
            return esi_name

        extra_fk_mappings = cls._eve_universe_meta_attr("fk_mappings")
        if not extra_fk_mappings:
            extra_fk_mappings = {}

        mappings = {
            x.name: (convert_to_esi_name(x.name, extra_fk_mappings), x.related_model)
            for x in cls._meta.get_fields()
            if isinstance(x, models.ForeignKey)
        }
        return mappings

    @classmethod
    def _field_names_not_pk(cls) -> set:
        """returns field names excl. PK, FK to parent, and auto created fields"""
        return {
            x.name
            for x in cls._meta.get_fields()
            if not x.auto_created
            and (not hasattr(x, "primary_key") or x.primary_key is False)
            and x.name not in {"last_updated"}
            and "name_" not in x.name
        }

    @classmethod
    def functional_pk(cls) -> set:
        """returns the set of fields that form the function pk"""
        functional_pk = cls._eve_universe_meta_attr("functional_pk")
        return functional_pk if functional_pk else set()

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


class EveUniverseModel(EveUniverseBaseModel):

    id = models.PositiveIntegerField(primary_key=True, help_text="Eve Online ID")
    name = models.CharField(max_length=100, help_text="Eve Online name")
    last_updated = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        help_text="When this object was last updated from ESI",
        db_index=True,
    )

    objects = EveUniverseModelManager()

    class Meta:
        abstract = True

    def __repr__(self):
        return "{}(id={}, name='{}')".format(
            self.__class__.__name__, self.id, self.name
        )

    def __str__(self):
        return self.name

    @classmethod
    def esi_method(cls) -> str:
        return cls._eve_universe_meta_attr("esi_method", is_mandatory=True)

    @classmethod
    def child_mappings(cls) -> dict:
        """returns the mapping of children for this class"""
        mappings = cls._eve_universe_meta_attr("children")
        return mappings if mappings else dict()

    @classmethod
    def inline_objects(cls) -> dict:
        """returns the inline objects if any"""
        inline_objects = cls._eve_universe_meta_attr("inline_objects")
        return inline_objects if inline_objects else dict()

    @classmethod
    def convert_values(cls, data_object: dict) -> dict:
        """ convert values of eve data objects"""
        # replace None with "" for CharFields
        char_fields = cls._char_fields()
        for field, value in data_object.items():
            if field in char_fields and value is None:
                data_object[field] = ""

        return data_object

    @classmethod
    def _char_fields(cls) -> set:
        """returns list of fields that are of type CharField"""
        return {
            f.name
            for f in cls._meta.get_fields(include_parents=False)
            if isinstance(f, (models.CharField, models.TextField))
        }


class EveAncestries(EveUniverseModel):
    """"Ancestry in Eve Online"""

    eve_bloodline = models.ForeignKey("EveBloodline", on_delete=models.CASCADE)
    description = models.TextField()
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    short_description = models.TextField(default="")

    objects = EveUniverseListManager()

    class EveUniverseMeta:
        esi_pk = "id"
        esi_method = "get_universe_ancestries"
        fk_mappings = {"eve_bloodline": "bloodline_id"}


class EveAsteroidBelt(EveUniverseModel):
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
        esi_method = "get_universe_asteroid_belts_asteroid_belt_id"
        fk_mappings = {"eve_solar_system": "system_id"}
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveBloodline(EveUniverseModel):
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

    objects = EveUniverseListManager()

    class EveUniverseMeta:
        esi_pk = "bloodline_id"
        esi_method = "get_universe_bloodlines"
        fk_mappings = {"eve_race": "race_id", "eve_ship_type": "ship_type_id"}


class EveCategory(EveUniverseModel):
    """category in Eve Online"""

    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "category_id"
        esi_method = "get_universe_categories_category_id"
        children = {"groups": "EveGroup"}


class EveConstellation(EveUniverseModel):
    """constellation in Eve Online"""

    eve_region = models.ForeignKey("EveRegion", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "constellation_id"
        esi_method = "get_universe_constellations_constellation_id"

        children = {"systems": "EveSolarSystem"}


class EveFaction(EveUniverseModel):
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

    objects = EveUniverseListManager()

    class EveUniverseMeta:
        esi_pk = "faction_id"
        esi_method = "get_universe_factions"
        fk_mappings = {"eve_solar_system": "solar_system_id"}


class EveGroup(EveUniverseModel):
    """group in Eve Online"""

    eve_category = models.ForeignKey("EveCategory", on_delete=models.CASCADE)
    published = models.BooleanField()

    class EveUniverseMeta:
        esi_pk = "group_id"
        esi_method = "get_universe_groups_group_id"
        children = {"types": "EveType"}


class EveMoon(EveUniverseModel):
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
        esi_method = "get_universe_moons_moon_id"
        fk_mappings = {"eve_solar_system": "system_id"}
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveRace(EveUniverseModel):
    """"faction in Eve Online"""

    alliance_id = models.PositiveIntegerField(db_index=True)
    description = models.TextField()

    objects = EveUniverseListManager()

    class EveUniverseMeta:
        esi_pk = "race_id"
        esi_method = "get_universe_races"


class EvePlanet(EveUniverseModel):
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
        esi_method = "get_universe_planets_planet_id"
        fk_mappings = {"eve_solar_system": "system_id"}
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveRegion(EveUniverseModel):
    """region in Eve Online"""

    description = models.TextField(default="")

    class EveUniverseMeta:
        esi_pk = "region_id"
        esi_method = "get_universe_regions_region_id"
        children = {"constellations": "EveConstellation"}


class EveSolarSystem(EveUniverseModel):
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
        esi_method = "get_universe_systems_system_id"
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }
        children = {"planets": "EvePlanet"}

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


class EveStar(EveUniverseModel):
    """"star in Eve Online"""

    age = models.PositiveIntegerField()
    luminosity = models.FloatField()
    radius = models.PositiveIntegerField()
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)
    spectral_class = models.CharField(max_length=16)
    temperature = models.PositiveIntegerField()
    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = "star_id"
        esi_method = "get_universe_stars_star_id"
        fk_mappings = {"eve_solar_system": "solar_system_id", "eve_type": "type_id"}


class EveStargate(EveUniverseModel):
    """"Stargate in Eve Online"""

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
        esi_method = "get_universe_stargates_stargate_id"
        fk_mappings = {"eve_solar_system": "system_id", "eve_type": "type_id"}
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveStargateDestination(models.Model):
    """Destination of a stargate in Eve Online"""

    eve_stargate = models.ForeignKey("EveStargate", on_delete=models.CASCADE)
    eve_solar_system = models.ForeignKey("EveSolarSystem", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_stargate", "eve_solar_system"], name="functional PK"
            )
        ]


class EveStation(EveUniverseModel):
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
        esi_method = "get_universe_stations_station_id"
        fk_mappings = {"eve_solar_system": "system_id", "eve_race": "race_id"}
        field_mappings = {
            "position_x": ("position", "x"),
            "position_y": ("position", "y"),
            "position_z": ("position", "z"),
        }


class EveType(EveUniverseModel):
    """Type in Eve Online"""

    capacity = models.FloatField(default=None, null=True)
    eve_group = models.ForeignKey("EveGroup", on_delete=models.CASCADE)
    graphic_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    icon_id = models.PositiveIntegerField(default=None, null=True, db_index=True)
    market_group_id = models.PositiveIntegerField(
        default=None, null=True, db_index=True
    )
    mass = models.FloatField(default=None, null=True)
    packaged_volume = models.FloatField(default=None, null=True)
    portion_size = models.PositiveIntegerField(default=None, null=True)
    radius = models.FloatField(default=None, null=True)
    published = models.BooleanField()
    volume = models.FloatField(default=None, null=True)

    class EveUniverseMeta:
        esi_pk = "type_id"
        esi_method = "get_universe_types_type_id"
        inline_objects = {
            "dogma_attributes": "EveTypeDogmaAttributes",
            "dogma_effects": "EveTypeDogmaEffects",
        }


class DogmaAttributes(EveUniverseBaseModel):
    """Dogma attribute in Eve Online"""

    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)
    attribute_id = models.PositiveIntegerField(db_index=True)
    value = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "attribute_id"], name="functional PK"
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        esi_pk = "attribute_id"

    def __repr__(self) -> str:
        return (
            f"DogmaAttributes(eve_type='{self.eve_type}', "
            f"attribute_id={self.attribute_id})"
        )


class DogmaEffects(EveUniverseBaseModel):
    """Dogma effect in Eve Online"""

    eve_type = models.ForeignKey("EveType", on_delete=models.CASCADE)
    effect_id = models.PositiveIntegerField(db_index=True)
    is_default = models.BooleanField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["eve_type", "effect_id"], name="functional PK"
            )
        ]

    class EveUniverseMeta:
        parent_fk = "eve_type"
        esi_pk = "effect_id"

    def __repr__(self) -> str:
        return (
            f"DogmaEffects(eve_type='{self.eve_type}', " f"effect_id={self.effect_id})"
        )
