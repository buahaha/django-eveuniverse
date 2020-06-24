from collections import namedtuple
import logging

from django.db import models

from bravado.exception import HTTPNotFound

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import LoggerAddTag, make_logger_prefix


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
                            if hasattr(ParentClass.objects, "update_or_create_esi"):
                                value, _ = ParentClass.objects.update_or_create_esi(
                                    esi_value,
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
        id: int,
        *,
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
        id: int,
        *,
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
            defaults = self._defaults_from_esi_obj(eve_data_obj)
            obj, created = self.update_or_create(id=id, defaults=defaults)
            inline_objects = self.model.inline_objects()
            if inline_objects:
                self._update_or_create_inline_objects(
                    primary_eve_data_obj=eve_data_obj,
                    primary_obj=obj,
                    inline_objects=inline_objects,
                )
            if include_children:
                self._update_or_create_children(
                    eve_data_obj=eve_data_obj,
                    include_children=include_children,
                    wait_for_children=wait_for_children,
                )

        except Exception as ex:
            logger.warn(
                add_prefix("Failed to update or create: %s" % ex), exc_info=True
            )
            raise ex

        return obj, created

    def _fetch_from_esi(self, id) -> object:
        """make request to ESI and return response data"""
        args = {self.model.esi_pk(): id}
        esi_data = getattr(
            getattr(esi.client, self.model.esi_route_category()),
            self.model.esi_route_method(),
        )(**args).results()
        return esi_data

    def _handle_list_endpoints(self, id, esi_data) -> object:
        is_list_endpoint = self.model._eve_universe_meta_attr("is_list_endpoint")
        if not is_list_endpoint:
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
        self, primary_eve_data_obj: dict, primary_obj: object, inline_objects: dict,
    ) -> None:
        from . import models as eveuniverse_models

        for inline_field, model_name in inline_objects.items():
            if (
                inline_field in primary_eve_data_obj
                and primary_eve_data_obj[inline_field]
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

                for eve_data_obj in primary_eve_data_obj[inline_field]:
                    args = {parent_fk: primary_obj}
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
        self, eve_data_obj: dict, include_children: bool, wait_for_children: bool
    ) -> None:
        """updates or creates child objects specified in eve mapping"""
        from . import models as eveuniverse_models

        for key, child_class in self.model.children().items():
            for id in eve_data_obj[key]:
                if wait_for_children:
                    ChildClass = getattr(eveuniverse_models, child_class)
                    ChildClass.objects.update_or_create_esi(
                        id=id,
                        include_children=include_children,
                        wait_for_children=wait_for_children,
                    )
                else:
                    load_eve_entity.delay(child_class, id)

    def update_or_create_all_esi(
        self, *, include_children: bool = False, wait_for_children: bool = False,
    ) -> None:
        """updates or creates all objects of this class from ESI
        
        include_children: if child objects should be updated/created as well 
        (if any)
        wait_for_children: when true child objects will be created blocking (if any), 
        else async
        """
        add_prefix = make_logger_prefix(f"{self.model.__name__}")
        is_list_endpoint = self.model._eve_universe_meta_attr("is_list_endpoint")
        if is_list_endpoint:
            try:
                eve_data_objects = getattr(
                    esi.client.Universe, self.model.esi_path()
                )().results()

                for eve_data_obj in eve_data_objects:
                    id = eve_data_obj[self.model.esi_pk()]
                    defaults = self.model.convert_values(
                        self._defaults_from_esi_obj(eve_data_obj,)
                    )
                    obj, _ = self.update_or_create(id=id, defaults=defaults)

            except Exception as ex:
                logger.warn(add_prefix("Failed to update or create: %s" % ex))
                raise ex
        else:
            NotImplementedError()


class EveMoonManager(EveUniverseEntityModelManager):
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
            if "moons" in planet and id in planet["moons"]:
                esi_data["planet_id"] = planet["planet_id"]
                return esi_data

        raise ValueError(
            f"Failed to find moon {id} in solar system response for {system_id} "
            f"- data error"
        )


class EveStationManager(EveUniverseEntityModelManager):
    """For special handling of station services"""

    def _update_or_create_inline_objects(
        self, primary_eve_data_obj: dict, primary_obj: object, inline_objects: dict,
    ) -> None:
        from .models import EveStationService

        if "services" in primary_eve_data_obj:
            services = list()
            for service_name in primary_eve_data_obj["services"]:
                service, _ = EveStationService.objects.get_or_create(name=service_name)
                services.append(service)

            if services:
                primary_obj.services.add(*services)

