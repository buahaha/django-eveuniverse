from django.db import models

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverseModelManager(models.Manager):
    def get_or_create_esi(
        self, id: int, include_children: bool = True, wait_for_children: bool = True,
    ) -> tuple:
        """gets or creates eve universe object fetched from ESI if needed. 
        Will always get/create parent objects.
        
        id: Eve Online ID of object

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
        self, id: int, include_children: bool = True, wait_for_children: bool = True,
    ) -> tuple:
        """updates or creates Eve Universe object with data fetched from ESI. 
        Will always update/create children and get/create parent objects.

        id: Eve Online ID of object

        Returns: object, created
        """
        add_prefix = make_logger_prefix("%s(id=%s)" % (self.model.__name__, id))
        try:
            args = {self.model.esi_pk(): id}
            esi_category, esi_method = self.model.esi_path().split(".")
            eve_data_obj = getattr(getattr(esi.client, esi_category), esi_method)(
                **args
            ).results()
            defaults = self.model.convert_values(
                self.model.map_esi_fields_to_model(eve_data_obj)
            )
            obj, created = self.update_or_create(id=id, defaults=defaults)
            inline_objects = self.model.inline_objects()
            if inline_objects:
                self._update_or_create_inline_objects(eve_data_obj, obj, inline_objects)
            if include_children:
                self._update_or_create_children_async(
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
        self, primary_eve_data_obj, primary_obj, inline_objects
    ) -> None:
        from . import models as eveuniverse_models

        for inline_field, model_name in inline_objects.items():
            if (
                inline_field in primary_eve_data_obj
                and primary_eve_data_obj[inline_field]
            ):
                InlineModel = getattr(eveuniverse_models, model_name)
                parent_fk = InlineModel.parent_fk()
                functional_pk_mapping = InlineModel.functional_pk_mapping()
                fk_mappings = InlineModel.fk_mappings()
                non_pk_fields = {
                    field_name
                    for field_name in InlineModel._field_names_not_pk()
                    if field_name not in fk_mappings.keys()
                }
                ParentClass2 = fk_mappings[functional_pk_mapping[0]][1]
                for eve_data_obj in primary_eve_data_obj[inline_field]:
                    fk_2_id = eve_data_obj[functional_pk_mapping[1]]
                    try:
                        value_fk_2 = ParentClass2.objects.get(id=fk_2_id)
                    except ParentClass2.DoesNotExist:
                        if hasattr(ParentClass2.objects, "update_or_create_esi"):
                            value_fk_2, _ = ParentClass2.objects.update_or_create_esi(
                                fk_2_id
                            )
                        else:
                            value_fk_2 = None
                    args = {
                        parent_fk: primary_obj,
                        functional_pk_mapping[0]: value_fk_2,
                    }
                    args["defaults"] = {
                        field_name: eve_data_obj[field_name]
                        for field_name in non_pk_fields
                    }
                    InlineModel.objects.update_or_create(**args)

    def _update_or_create_children_async(
        self, eve_data_obj: dict, include_children: bool, wait_for_children: bool
    ) -> None:
        """updates or creates child objects specified in eve mapping"""
        from . import models as eveuniverse_models

        for key, child_class in self.model.child_mappings().items():
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


class EveUniverseListManager(models.Manager):
    """Alternative manager for entities that are not loaded via IDs from ESI, 
    but as list
    """

    def load_esi(self) -> None:
        """updates or creates all objects of this class from ESI"""
        add_prefix = make_logger_prefix(f"{self.model.__name__}")
        try:
            eve_data_objects = getattr(
                esi.client.Universe, self.model.esi_path()
            )().results()

            for eve_data_obj in eve_data_objects:
                id = eve_data_obj[self.model.esi_pk()]
                defaults = self.model.convert_values(
                    self.model.map_esi_fields_to_model(eve_data_obj)
                )
                obj, _ = self.update_or_create(id=id, defaults=defaults)

        except Exception as ex:
            logger.warn(add_prefix("Failed to update or create: %s" % ex))
            raise ex
