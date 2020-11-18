from collections import namedtuple
import datetime as dt
import logging
from typing import List, Iterable, Tuple, Optional

from django.db import models, transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now

from bravado.exception import HTTPNotFound

from . import __title__
from .app_settings import EVEUNIVERSE_BULK_METHODS_BATCH_SIZE
from .helpers import EveEntityNameResolver, get_or_create_esi_or_none
from .providers import esi
from .utils import chunks, LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(logging.getLogger(__name__), __title__)

FakeResponse = namedtuple("FakeResponse", ["status_code"])


class EveUniverseBaseModelManager(models.Manager):
    def _defaults_from_esi_obj(self, eve_data_obj: dict) -> dict:
        """compiles defaults from an esi data object for update/creating the model"""
        defaults = dict()
        for field_name, mapping in self.model._esi_mapping().items():
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
                            value = None
                            if mapping.create_related:
                                try:
                                    value, _ = ParentClass.objects.update_or_create_esi(
                                        id=esi_value,
                                        include_children=False,
                                        wait_for_children=True,
                                    )
                                except AttributeError:
                                    pass

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
    ) -> Tuple[models.Model, bool]:
        """gets or creates an eve universe object.

        The object is automatically fetched from ESI if it does not exist (blocking).
        Will always get/create parent objects.

        Args:
            id: Eve Online ID of object
            include_children: when needed to updated/created if child objects should be updated/created as well (if any)
            wait_for_children: when true child objects will be updated/created blocking (if any), else async

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        id = int(id)
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
        enabled_sections: Iterable[str] = None,
    ) -> Tuple[models.Model, bool]:
        """updates or creates an Eve universe object by fetching it from ESI (blocking).
        Will always get/create parent objects

        Args:
            id: Eve Online ID of object
            include_children: if child objects should be updated/created as well (if any)
            wait_for_children: when true child objects will be updated/created blocking (if any), else async
            enabled_sections: Sections to load regardless of current settings, e.g. `EveUniverseEntityModel.LOAD_DOGMAS` will always load dogmas for EveTypes

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        id = int(id)
        enabled_sections = set(enabled_sections) if enabled_sections else set()
        add_prefix = make_logger_prefix("%s(id=%s)" % (self.model.__name__, id))
        try:
            eve_data_obj = self._transform_esi_response_for_list_endpoints(
                id, self._fetch_from_esi(id)
            )
            if eve_data_obj:
                defaults = self._defaults_from_esi_obj(eve_data_obj)
                obj, created = self.update_or_create(id=id, defaults=defaults)
                inline_objects = self.model._inline_objects(enabled_sections)
                if inline_objects:
                    self._update_or_create_inline_objects(
                        parent_eve_data_obj=eve_data_obj,
                        parent_obj=obj,
                        inline_objects=inline_objects,
                        wait_for_children=wait_for_children,
                    )
                if include_children:
                    self._update_or_create_children(
                        parent_eve_data_obj=eve_data_obj,
                        include_children=include_children,
                        wait_for_children=wait_for_children,
                        enabled_sections=enabled_sections,
                    )
            else:
                raise HTTPNotFound(
                    FakeResponse(status_code=404),
                    message=f"{self.model.__name__} object with id {id} not found",
                )

        except Exception as ex:
            logger.warn(
                add_prefix("Failed to update or create: %s" % ex),
                exc_info=True,
            )
            raise ex

        return obj, created

    def _fetch_from_esi(self, id: int = None) -> object:
        """make request to ESI and return response data.
        Can handle raw ESI response from both list and normal endpoints.
        """
        if id and not self.model._is_list_only_endpoint():
            args = {self.model._esi_pk(): id}
        else:
            args = dict()
        category, method = self.model._esi_path_object()
        esi_data = getattr(
            getattr(esi.client, category),
            method,
        )(**args).results()
        return esi_data

    def _transform_esi_response_for_list_endpoints(self, id: int, esi_data) -> object:
        """Transforms raw ESI response from list endpoints if this is one
        else just passes the ESI response through
        """
        if not self.model._is_list_only_endpoint():
            return esi_data

        else:
            esi_pk = self.model._esi_pk()
            for row in esi_data:
                if esi_pk in row and row[esi_pk] == id:
                    return row

            raise HTTPNotFound(
                FakeResponse(status_code=404),
                message=f"{self.model.__name__} object with id {id} not found",
            )

    def _update_or_create_inline_objects(
        self,
        *,
        parent_eve_data_obj: dict,
        parent_obj: models.Model,
        inline_objects: dict,
        wait_for_children: bool,
    ) -> None:
        """updates_or_creates eve objects that are returns "inline" from ESI
        for the parent eve objects as defined for this parent model (if any)
        """
        from .tasks import (
            update_or_create_inline_object as task_update_or_create_inline_object,
        )

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
                InlineModel = self.model.get_model_class(model_name)
                esi_mapping = InlineModel._esi_mapping()
                parent_fk = None
                other_pk = None
                ParentClass2 = None
                for field_name, mapping in esi_mapping.items():
                    if mapping.is_pk:
                        if mapping.is_parent_fk:
                            parent_fk = field_name
                        else:
                            other_pk = (field_name, mapping)
                            ParentClass2 = mapping.related_model

                if not parent_fk or not other_pk:
                    raise ValueError(
                        "ESI Mapping for %s not valid: %s, %s"
                        % (
                            model_name,
                            parent_fk,
                            other_pk,
                        )
                    )

                parent2_model_name = ParentClass2.__name__ if ParentClass2 else None
                other_pk_info = {
                    "name": other_pk[0],
                    "esi_name": other_pk[1].esi_name,
                    "is_fk": other_pk[1].is_fk,
                }
                for eve_data_obj in parent_eve_data_obj[inline_field]:
                    if wait_for_children:
                        self._update_or_create_inline_object(
                            parent_obj_id=parent_obj.id,
                            parent_fk=parent_fk,
                            eve_data_obj=eve_data_obj,
                            other_pk_info=other_pk_info,
                            parent2_model_name=parent2_model_name,
                            inline_model_name=model_name,
                        )
                    else:
                        task_update_or_create_inline_object(
                            parent_obj_id=parent_obj.id,
                            parent_fk=parent_fk,
                            eve_data_obj=eve_data_obj,
                            other_pk_info=other_pk_info,
                            parent2_model_name=parent2_model_name,
                            inline_model_name=model_name,
                            parent_model_name=type(parent_obj).__name__,
                        )

    def _update_or_create_inline_object(
        self,
        parent_obj_id: int,
        parent_fk: str,
        eve_data_obj: dict,
        other_pk_info: dict,
        parent2_model_name: str,
        inline_model_name: str,
    ):
        """Updates or creates a single inline object.
        Will automatically create additional parent objects as needed
        """
        InlineModel = self.model.get_model_class(inline_model_name)

        args = {f"{parent_fk}_id": parent_obj_id}
        esi_value = eve_data_obj.get(other_pk_info["esi_name"])
        if other_pk_info["is_fk"]:
            ParentClass2 = self.model.get_model_class(parent2_model_name)
            try:
                value = ParentClass2.objects.get(id=esi_value)
            except ParentClass2.DoesNotExist:
                try:
                    value, _ = ParentClass2.objects.update_or_create_esi(id=esi_value)
                except AttributeError:
                    value = None
        else:
            value = esi_value

        args[other_pk_info["name"]] = value
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
        enabled_sections: Iterable[str] = None,
    ) -> None:
        """updates or creates child objects as defined for this parent model (if any)"""
        from .tasks import (
            update_or_create_eve_object as task_update_or_create_eve_object,
        )

        if not parent_eve_data_obj:
            raise ValueError(
                "%s: Tried to create children from empty parent object"
                % self.model.__name__,
            )

        for key, child_class in self.model._children().items():
            if key in parent_eve_data_obj and parent_eve_data_obj[key]:
                for id in parent_eve_data_obj[key]:
                    if wait_for_children:
                        ChildClass = self.model.get_model_class(child_class)
                        ChildClass.objects.update_or_create_esi(
                            id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                            enabled_sections=enabled_sections,
                        )

                    else:
                        task_update_or_create_eve_object.delay(
                            child_class,
                            id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                            enabled_sections=list(enabled_sections),
                        )

    def update_or_create_all_esi(
        self,
        *,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> None:
        """updates or creates all objects of this class from ESI.

        Loading all objects can take a long time. Use with care!

        Args:
            include_children: if child objects should be updated/created as well (if any)
            wait_for_children: when false all objects will be loaded async, else blocking
        """
        from .tasks import update_or_create_eve_object

        add_prefix = make_logger_prefix(f"{self.model.__name__}")
        if self.model._is_list_only_endpoint():
            try:
                esi_pk = self.model._esi_pk()
                for eve_data_obj in self._fetch_from_esi():
                    args = {"id": eve_data_obj[esi_pk]}
                    args["defaults"] = self._defaults_from_esi_obj(eve_data_obj)
                    self.update_or_create(**args)

            except Exception as ex:
                logger.warn(
                    add_prefix("Failed to update or create: %s" % ex),
                    exc_info=True,
                )
                raise ex
        else:
            if self.model._has_esi_path_list():
                category, method = self.model._esi_path_list()
                ids = getattr(
                    getattr(esi.client, category),
                    method,
                )().results()
                for id in ids:
                    if wait_for_children:
                        self.update_or_create_esi(
                            id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
                    else:
                        update_or_create_eve_object.delay(
                            model_name=self.model.__name__,
                            entity_id=id,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
            else:
                raise TypeError(
                    f"ESI does not provide a list endpoint for {self.model.__name__}"
                )

    def bulk_get_or_create_esi(
        self,
        *,
        ids: List[int],
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> models.QuerySet:
        """Gets or creates objects in bulk.

        Nonexisting objects will be fetched from ESI (blocking).
        Will always get/create parent objects.

        Args:
            ids: List of valid IDs of Eve objects
            include_children: when needed to updated/created if child objects should be updated/created as well (if any)
            wait_for_children: when true child objects will be updated/created blocking (if any), else async

        Returns:
            Queryset with all requested eve objects
        """
        ids = set(ids)
        existing_ids = set(self.filter(id__in=ids).values_list("id", flat=True))
        for id in ids.difference(existing_ids):
            self.update_or_create_esi(
                id=int(id),
                include_children=include_children,
                wait_for_children=wait_for_children,
            )

        return self.filter(id__in=ids)


class EvePlanetManager(EveUniverseEntityModelManager):
    def _fetch_from_esi(self, id) -> object:
        from .models import EveSolarSystem

        esi_data = super()._fetch_from_esi(id)
        # no need to proceed if all children have been disabled
        if not self.model._children():
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
    def __init__(self, property_name: str) -> None:
        super().__init__()
        self._my_property_name = property_name

    def _fetch_from_esi(self, id: int) -> object:
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
                and planet[self._my_property_name]
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
        enabled_sections: Iterable[str] = None,
    ) -> Tuple[models.Model, bool]:
        """updates or creates an EveStargate object by fetching it from ESI (blocking).
        Will always get/create parent objects

        Args:
            id: Eve Online ID of object
            include_children: (no effect)
            wait_for_children: (no effect)

        Returns:
            A tuple consisting of the requested object and a created flag
        """
        obj, created = super().update_or_create_esi(
            id=int(id),
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
        self,
        *,
        parent_eve_data_obj: dict,
        parent_obj: models.Model,
        inline_objects: dict,
        wait_for_children: bool,
    ) -> None:
        """updates_or_creates station service objects for EveStations"""
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
        """Updates all Eve entity objects in this queryset from ESI"""
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
                try:
                    self.update_or_create(
                        id=item["id"],
                        defaults={"name": item["name"], "category": item["category"]},
                    )
                except IntegrityError:
                    pass

        return resolved_counter


class EveEntityManager(EveUniverseEntityModelManager):
    """Custom manager for EveEntity"""

    def get_queryset(self) -> models.QuerySet:
        return EveEntityQuerySet(self.model, using=self._db)

    def get_or_create_esi(
        self,
        *,
        id: int,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> Tuple[models.Model, bool]:
        """gets or creates an EvEntity object.

        The object is automatically fetched from ESI if it does not exist (blocking)
        or if it has not yet been resolved.

        Args:
            id: Eve Online ID of object

        Returns:
            A tuple consisting of the requested EveEntity object and a created flag
            Returns a None objects if the ID is invalid
        """
        id = int(id)
        try:
            obj = self.exclude(name="").get(id=id)
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
        enabled_sections: Iterable[str] = None,
    ) -> Tuple[Optional[models.Model], bool]:
        """updates or creates an EveEntity object by fetching it from ESI (blocking).

        Args:
            id: Eve Online ID of object
            include_children: (no effect)
            wait_for_children: (no effect)

        Returns:
            A tuple consisting of the requested object and a created flag
            When the ID is invalid the returned object will be None

        Exceptions:
            Raises all HTTP codes of ESI endpoint /universe/names except 404
        """
        id = int(id)
        logger.info("%s: Trying to resolve ID to EveEntity with ESI", id)
        try:
            result = esi.client.Universe.post_universe_names(ids=[id]).results()
        except HTTPNotFound:
            logger.info("%s: ID is not valid", id)
            return None, False

        item = result[0]
        return self.update_or_create(
            id=item.get("id"),
            defaults={"name": item.get("name"), "category": item.get("category")},
        )

    def bulk_create_esi(self, ids: Iterable[int]) -> int:
        """bulk create and resolve multiple entities from ESI.
        Will also resolve existing entities, that have no name.

        Args:
            ids: List of valid EveEntity IDs

        Returns:
            Count of updated entities
        """
        ids = set(map(int, ids))
        with transaction.atomic():
            existing_ids = set(self.filter(id__in=ids).values_list("id", flat=True))
            new_ids = ids.difference(existing_ids)
            if new_ids:
                objects = [self.model(id=id) for id in new_ids]
                self.bulk_create(
                    objects, batch_size=EVEUNIVERSE_BULK_METHODS_BATCH_SIZE
                )
                to_update_qs = self.filter(id__in=new_ids) | self.filter(
                    id__in=ids.difference(new_ids), name=""
                )
                return to_update_qs.update_from_esi()

        return 0

    def update_or_create_all_esi(
        self,
        *,
        include_children: bool = False,
        wait_for_children: bool = True,
    ) -> None:
        """not implemented - do not use"""
        raise NotImplementedError()

    def bulk_update_new_esi(self) -> int:
        """updates all unresolved EveEntity objects in the database from ESI.

        Returns:
            Count of updated entities.
        """
        return self.filter(name="").update_from_esi()

    def bulk_update_all_esi(self):
        """Updates all EveEntity objects in the database from ESI.

        Returns:
            Count of updated entities.
        """
        return self.all().update_from_esi()

    def resolve_name(self, id: int) -> str:
        """return the name for the given Eve entity ID
        or an empty string if ID is not valid
        """
        if id is not None:
            obj, _ = self.get_or_create_esi(id=int(id))
            if obj:
                return obj.name

        return ""

    def bulk_resolve_names(self, ids: Iterable[int]) -> EveEntityNameResolver:
        """returns a map of IDs to names in a resolver object for given IDs

        Args:
            ids: List of valid EveEntity IDs

        Returns:
            EveEntityNameResolver object helpful for quick resolving a large amount
            of IDs
        """
        ids = set(ids)
        self.bulk_create_esi(ids)
        return EveEntityNameResolver(
            {
                row[0]: row[1]
                for row in self.filter(id__in=ids).values_list("id", "name")
            }
        )


class EveMarketPriceManager(models.Manager):
    def update_from_esi(self, minutes_until_stale: int = None) -> int:
        """Updates market prices from ESI. Will only create new price objects for EveTypes that already exist in the database.

        Args:
            minutes_until_stale: only prices older then given minutes are regarding as stale and will be updated. Will use default (60) if not specified.

        Returns:
            Count of updated types
        """
        from .models import EveType

        if minutes_until_stale is None:
            minutes_until_stale = self.model.DEFAULT_MINUTES_UNTIL_STALE

        logger.info("Fetching market prices from ESI")
        entries = esi.client.Market.get_markets_prices().results()
        if not entries:
            return 0

        entries_2 = {int(x["type_id"]): x for x in entries if "type_id" in x}
        with transaction.atomic():
            existing_types_ids = set(EveType.objects.values_list("id", flat=True))
            relevant_prices_ids = set(entries_2.keys()).intersection(existing_types_ids)
            deadline = now() - dt.timedelta(minutes=minutes_until_stale)
            current_prices_ids = set(
                self.filter(updated_at__gt=deadline).values_list(
                    "eve_type_id", flat=True
                )
            )
            need_updating_ids = relevant_prices_ids.difference(current_prices_ids)
            if not need_updating_ids:
                logger.info("Market prices are up to date")
                return 0

            logger.info("Updating market prices for %s types", len(need_updating_ids))
            self.filter(eve_type_id__in=need_updating_ids).delete()
            market_prices = [
                self.model(
                    eve_type=get_or_create_esi_or_none("type_id", entry, EveType),
                    adjusted_price=entry.get("adjusted_price"),
                    average_price=entry.get("average_price"),
                )
                for type_id, entry in entries_2.items()
                if type_id in need_updating_ids
            ]
            self.bulk_create(
                market_prices, batch_size=EVEUNIVERSE_BULK_METHODS_BATCH_SIZE
            )
            return len(market_prices)
