from collections import namedtuple
import logging

from django.db import models

from bravado.exception import HTTPNotFound

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import chunks, LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(logging.getLogger(__name__), __title__)

FakeResponse = namedtuple("FakeResponse", ["status_code"])


class EveUniverseBaseModelManager(models.Manager):
    def _defaults_from_esi_obj(self, eve_data_obj: dict) -> dict:
        """compiles defaults from an esi data object for update/creating the model"""
        defaults = dict()
        for field_name, mapping in self.model.esi_mapping().items():
            if not mapping.is_pk:
                if not isinstance(mapping.esi_name, tuple):
                    if mapping.esi_name in eve_data_obj:
                        esi_value = eve_data_obj[mapping.esi_name]
                    else:
                        esi_value = None
                else:
                    if (
                        mapping.esi_name[0] in eve_data_obj
                        and mapping.esi_name[1] in eve_data_obj[mapping.esi_name[0]]
                    ):
                        esi_value = eve_data_obj[mapping.esi_name[0]][
                            mapping.esi_name[1]
                        ]
                    else:
                        esi_value = None

                if esi_value is not None:
                    if mapping.is_fk:
                        ParentClass = mapping.related_model
                        try:
                            value = ParentClass.objects.get(id=esi_value)
                        except ParentClass.DoesNotExist:
                            if mapping.create_related and hasattr(
                                ParentClass.objects, "update_or_create_esi"
                            ):
                                value, _ = ParentClass.objects.update_or_create_esi(
                                    id=esi_value,
                                    include_children=False,
                                    wait_for_children=True,
                                )
                            else:
                                value = None

                    else:
                        if mapping.is_charfield and esi_value is None:
                            value = ""
                        else:
                            value = esi_value

                    defaults[field_name] = value

        return defaults


class EveUniverseEntityModelManager(EveUniverseBaseModelManager):
    def get_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> tuple:
        """gets or creates eve universe object fetched from ESI if needed. 
        Will always get/create parent objects.
        
        id: Eve Online ID of object
        include_children: if child objects should be updated/created as well (if any)
        when an update is required
        wait_for_children: when true child objects will be created blocking (if any), 
        else async

        Returns: object, created        
        """
        try:
            obj = self.get(id=id)
            created = False
        except self.model.DoesNotExist:
            obj, created = self.update_or_create_esi(
                id=id,
                include_children=include_children,
                wait_for_children=wait_for_children,
            )

        return obj, created

    def update_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> tuple:
        """updates or creates Eve Universe object with data fetched from ESI. 
        Will always get/create parent objects.

        id: Eve Online ID of object
        include_children: if child objects should be updated/created as well (if any)
        wait_for_children: when true child objects will be created blocking (if any), 
        else async

        Returns: object, created
        """
        add_prefix = make_logger_prefix("%s(id=%s)" % (self.model.__name__, id))
        try:
            eve_data_obj = self._handle_list_endpoints(id, self._fetch_from_esi(id))
            if eve_data_obj:
                defaults = self._defaults_from_esi_obj(eve_data_obj)
                obj, created = self.update_or_create(id=id, defaults=defaults)
                inline_objects = self.model.inline_objects()
                if inline_objects:
                    self._update_or_create_inline_objects(
                        parent_eve_data_obj=eve_data_obj,
                        parent_obj=obj,
                        inline_objects=inline_objects,
                    )
                if eve_data_obj and include_children:
                    self._update_or_create_children(
                        parent_eve_data_obj=eve_data_obj,
                        include_children=include_children,
                        wait_for_children=wait_for_children,
                    )

        except Exception as ex:
            logger.warn(
                add_prefix("Failed to update or create: %s" % ex), exc_info=True,
            )
            raise ex

        return obj, created

    def _fetch_from_esi(self, id=None) -> object:
        """make request to ESI and return response data"""
        if id and not self.model.is_list_only_endpoint():
            args = {self.model.esi_pk(): id}
        else:
            args = dict()
        category, method = self.model.esi_path_object()
        esi_data = getattr(getattr(esi.client, category), method,)(**args).results()
        return esi_data

    def _handle_list_endpoints(self, id, esi_data) -> object:
        if not self.model.is_list_only_endpoint():
            return esi_data

        else:
            esi_pk = self.model.esi_pk()
            for row in esi_data:
                if esi_pk in row and row[esi_pk] == id:
                    return row

            raise HTTPNotFound(
                FakeResponse(status_code=404),
                message=f"{self.model.__name__} object with id {id} not found",
            )

    def _update_or_create_inline_objects(
        self, *, parent_eve_data_obj: dict, parent_obj: object, inline_objects: dict,
    ) -> None:
        from . import models as eveuniverse_models

        if not parent_eve_data_obj or not parent_obj:
            raise ValueError(
                "%s: Tried to create inline object from empty parent object"
                % self.model.__name__,
            )

        for inline_field, model_name in inline_objects.items():
            if (
                inline_field in parent_eve_data_obj
                and parent_eve_data_obj[inline_field]
            ):
                InlineModel = getattr(eveuniverse_models, model_name)
                esi_mapping = InlineModel.esi_mapping()
                for field_name, mapping in esi_mapping.items():
                    if mapping.is_pk:
                        if mapping.is_parent_fk:
                            parent_fk = field_name
                        else:
                            other_pk = (field_name, mapping)
                            ParentClass2 = mapping.related_model

                for eve_data_obj in parent_eve_data_obj[inline_field]:
                    args = {parent_fk: parent_obj}
                    esi_value = eve_data_obj[other_pk[1].esi_name]
                    if other_pk[1].is_fk:
                        try:
                            value = ParentClass2.objects.get(id=esi_value)
                        except ParentClass2.DoesNotExist:
                            if hasattr(ParentClass2.objects, "update_or_create_esi"):
                                (value, _,) = ParentClass2.objects.get_or_create_esi(
                                    id=esi_value
                                )
                            else:
                                value = None
                    else:
                        value = esi_value

                    args[other_pk[0]] = value
                    args["defaults"] = InlineModel.objects._defaults_from_esi_obj(
                        eve_data_obj,
                    )
                    InlineModel.objects.update_or_create(**args)

    def _update_or_create_children(
        self,
        *,
        parent_eve_data_obj: dict,
        include_children: bool,
        wait_for_children: bool,
    ) -> None:
        """updates or creates child objects specified in eve mapping"""
        from . import models as eveuniverse_models

        if not parent_eve_data_obj:
            raise ValueError(
                "%s: Tried to create children from empty parent object"
                % self.model.__name__,
            )

        for key, child_class in self.model.children().items():
            if key in parent_eve_data_obj and parent_eve_data_obj[key]:
                for id in parent_eve_data_obj[key]:
                    if wait_for_children:
                        ChildClass = getattr(eveuniverse_models, child_class)
                        ChildClass.objects.update_or_create_esi(
                            id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
                    else:
                        load_eve_entity.delay(
                            child_class,
                            id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )

    def update_or_create_all_esi(
        self, *, include_children: bool = False, wait_for_children: bool = True,
    ) -> None:
        """updates or creates all objects of this class from ESI
        
        include_children: if child objects should be updated/created as well 
        (if any)
        wait_for_children: when true child objects will be created blocking (if any), 
        else async
        """
        add_prefix = make_logger_prefix(f"{self.model.__name__}")
        if self.model.is_list_only_endpoint():
            try:
                esi_pk = self.model.esi_pk()
                for eve_data_obj in self._fetch_from_esi():
                    args = {"id": eve_data_obj[esi_pk]}
                    args["defaults"] = self._defaults_from_esi_obj(eve_data_obj)
                    obj, _ = self.update_or_create(**args)

            except Exception as ex:
                logger.warn(
                    add_prefix("Failed to update or create: %s" % ex), exc_info=True,
                )
                raise ex
        else:
            if self.model.has_esi_path_list():
                category, method = self.model.esi_path_list()
                ids = getattr(getattr(esi.client, category), method,)().results()
                for id in ids:
                    if wait_for_children:
                        self.update_or_create_esi(
                            id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
                    else:
                        load_eve_entity.delay(
                            model_name=self.model.__name__,
                            entity_id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
            else:
                raise TypeError(
                    f"ESI does not provide a list endpoint for {self.model.__name__}"
                )


class EvePlanetManager(EveUniverseEntityModelManager):
    def _fetch_from_esi(self, id):
        from .models import EveSolarSystem

        esi_data = super()._fetch_from_esi(id)
        # no need to proceed if all children have been disabled
        if not self.model.children():
            return esi_data

        if "system_id" not in esi_data:
            raise ValueError("system_id not found in moon response - data error")

        system_id = esi_data["system_id"]
        solar_system_data = EveSolarSystem.objects._fetch_from_esi(system_id)
        if "planets" not in solar_system_data:
            raise ValueError("planets not found in solar system response - data error")

        for planet in solar_system_data["planets"]:
            if planet["planet_id"] == id:
                if "moons" in planet:
                    esi_data["moons"] = planet["moons"]

                if "asteroid_belts" in planet:
                    esi_data["asteroid_belts"] = planet["asteroid_belts"]

                return esi_data

        raise ValueError(
            f"Failed to find moon {id} in solar system response for {system_id} "
            f"- data error"
        )


class EvePlanetChildrenManager(EveUniverseEntityModelManager):
    def __init__(self, property_name: str):
        super().__init__()
        self._my_property_name = property_name

    def _fetch_from_esi(self, id):
        from .models import EveSolarSystem

        esi_data = super()._fetch_from_esi(id)
        if "system_id" not in esi_data:
            raise ValueError("system_id not found in moon response - data error")

        system_id = esi_data["system_id"]
        solar_system_data = EveSolarSystem.objects._fetch_from_esi(system_id)
        if "planets" not in solar_system_data:
            raise ValueError("planets not found in solar system response - data error")

        for planet in solar_system_data["planets"]:
            if (
                self._my_property_name in planet
                and id in planet[self._my_property_name]
            ):
                esi_data["planet_id"] = planet["planet_id"]
                return esi_data

        raise ValueError(
            f"Failed to find moon {id} in solar system response for {system_id} "
            f"- data error"
        )


class EveStargateManager(EveUniverseEntityModelManager):
    """For special handling of relations"""

    def update_or_create_esi(
        self,
        id: int,
        *,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> tuple:
        """If our destination is not null, then we also need to update 
        the other stargate's relation to us
        """
        obj, created = super().update_or_create_esi(
            id=id,
            include_children=include_children,
            wait_for_children=wait_for_children,
        )
        if obj:
            if obj.destination_eve_stargate is not None:
                obj.destination_eve_stargate.destination_eve_stargate = obj

                if obj.eve_solar_system is not None:
                    obj.destination_eve_stargate.destination_eve_solar_system = (
                        obj.eve_solar_system
                    )
                obj.destination_eve_stargate.save()

        return obj, created


class EveStationManager(EveUniverseEntityModelManager):
    """For special handling of station services"""

    def _update_or_create_inline_objects(
        self, *, parent_eve_data_obj: dict, parent_obj: object, inline_objects: dict,
    ) -> None:
        from .models import EveStationService

        if "services" in parent_eve_data_obj:
            services = list()
            for service_name in parent_eve_data_obj["services"]:
                service, _ = EveStationService.objects.get_or_create(name=service_name)
                services.append(service)

            if services:
                parent_obj.services.add(*services)


class EveEntityQuerySet(models.QuerySet):
    """Custom queryset for EveEntity"""

    MAX_DEPTH = 5

    def update_from_esi(self) -> int:
        ids = list(self.values_list("id", flat=True))
        if not ids:
            return 0
        else:
            logger.info("Updating %d entities from ESI", len(ids))
            resolved_counter = 0
            for chunk_ids in chunks(ids, 1000):
                logger.debug(
                    "Trying to resolve the following IDs from ESI:\n%s", chunk_ids
                )
                resolved_counter = self._resolve_entities_from_esi(chunk_ids)
            return resolved_counter

        return resolved_counter

    def _resolve_entities_from_esi(self, ids: list, depth: int = 1):
        resolved_counter = 0
        try:
            items = esi.client.Universe.post_universe_names(ids=ids).results()
        except HTTPNotFound:
            # if API fails to resolve all IDs, we divide and conquer,
            # trying to resolve each half of the ids seperately
            if len(ids) > 1 and depth < self.MAX_DEPTH:
                resolved_counter += self._resolve_entities_from_esi(ids[::2], depth + 1)
                resolved_counter += self._resolve_entities_from_esi(
                    ids[1::2], depth + 1
                )
            else:
                logger.warning("Failed to resolve invalid IDs: %s", ids)
        else:
            resolved_counter += len(items)
            for item in items:
                self.update_or_create(
                    id=item["id"],
                    defaults={"name": item["name"], "category": item["category"]},
                )
        return resolved_counter


class EveEntityManager(EveUniverseEntityModelManager):
    """Custom manager for EveEntity"""

    def get_queryset(self):
        return EveEntityQuerySet(self.model, using=self._db)

    def update_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> tuple:
        """updated or creates object from ESI and returns it with created flag"""
        obj, created = self.update_or_create(id=id)
        self.filter(id=id).update_from_esi()
        obj.refresh_from_db()
        return obj, created

    def bulk_create_from_esi(self, *, ids: list):
        """bulk create multiple entities from ESI. Returns count of updated entities"""
        objects = [self.model(id=id) for id in ids]
        self.bulk_create(objects, ignore_conflicts=True)
        return self.filter(id__in=ids).update_from_esi()

    def update_or_create_all_esi(
        self, *, include_children: bool = False, wait_for_children: bool = True,
    ) -> None:
        """not implemented"""
        raise NotImplementedError()

    def bulk_update_new_from_esi(self):
        """updates all new entities from ESI. Returns count of updated entities."""
        return self.filter(name="").update_from_esi()

    def bulk_update_all_from_esi(self):
        """updates all existing entities from ESI. Returns count of updated entities."""
        return self.all.update_from_esi()
