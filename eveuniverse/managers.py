from django.db import models

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverseBaseModelManager(models.Manager):
    def _defaults_from_esi_obj(
        self, eve_data_obj: dict, include_children: bool, wait_for_children: bool,
    ) -> dict:
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
                                    include_children=include_children,
                                    wait_for_children=wait_for_children,
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
        wait_for_children: bool = False,
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
        wait_for_children: bool = False,
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
        esi_pk = self.model.esi_pk()
        try:
            args = {esi_pk: id}
            esi_data = getattr(
                getattr(esi.client, self.model.esi_route_category()),
                self.model.esi_route_method(),
            )(**args).results()
            is_list_endpoint = self.model._eve_universe_meta_attr("is_list_endpoint")
            if is_list_endpoint:
                eve_data_obj = None
                for row in esi_data:
                    if esi_pk in row and row[esi_pk] == id:
                        eve_data_obj = row
            else:
                eve_data_obj = esi_data

            defaults = self._defaults_from_esi_obj(
                eve_data_obj,
                include_children=include_children,
                wait_for_children=wait_for_children,
            )
            obj, created = self.update_or_create(id=id, defaults=defaults)
            inline_objects = self.model.inline_objects()
            if inline_objects and self.model.is_loading_inlines_enabled():
                self._update_or_create_inline_objects(
                    primary_eve_data_obj=eve_data_obj,
                    primary_obj=obj,
                    inline_objects=inline_objects,
                    include_children=include_children,
                    wait_for_children=wait_for_children,
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

    def _update_or_create_inline_objects(
        self,
        primary_eve_data_obj: dict,
        primary_obj: object,
        inline_objects: dict,
        include_children: bool,
        wait_for_children: bool,
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
                                (value, _,) = ParentClass2.objects.update_or_create_esi(
                                    id=esi_value,
                                    include_children=include_children,
                                    wait_for_children=wait_for_children,
                                )
                            else:
                                value = None
                    else:
                        value = esi_value

                    args[other_pk[0]] = value
                    args["defaults"] = InlineModel.objects._defaults_from_esi_obj(
                        eve_data_obj,
                        include_children=include_children,
                        wait_for_children=wait_for_children,
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
                        self._defaults_from_esi_obj(
                            eve_data_obj,
                            include_children=include_children,
                            wait_for_children=wait_for_children,
                        )
                    )
                    obj, _ = self.update_or_create(id=id, defaults=defaults)

            except Exception as ex:
                logger.warn(add_prefix("Failed to update or create: %s" % ex))
                raise ex
        else:
            NotImplementedError()
