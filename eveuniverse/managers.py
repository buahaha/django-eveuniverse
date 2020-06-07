from django.db import models

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverseModelManager(models.Manager):
    def get_or_create_esi(self, id: int) -> tuple:
        """gets or creates eve universe object fetched from ESI if needed. 
        Will always get/create parent objects.
        
        id: Eve Online ID of object

        Returns: object, created        
        """
        try:
            obj = self.get(id=id)
            created = False
        except self.model.DoesNotExist:
            obj, created = self.update_or_create_esi(id)

        return obj, created

    def update_or_create_esi(self, id: int, include_children: bool = True) -> tuple:
        """updates or creates Eve Universe object with data fetched from ESI. 
        Will always update/create children and get/create parent objects.

        id: Eve Online ID of object

        Returns: object, created
        """
        add_prefix = make_logger_prefix("%s(id=%d)" % (self.model.__name__, id))
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
                self._update_or_create_children_async(eve_data_obj)

        except Exception as ex:
            logger.warn(add_prefix("Failed to update or create: %s" % ex))
            raise ex

        return obj, created

    def _update_or_create_inline_objects(
        self, primary_eve_data_obj, primary_obj, inline_objects
    ) -> None:
        from . import models as eveuniverse_models

        for inline_field, model_name in inline_objects.items():
            InlineModel = getattr(eveuniverse_models, model_name)
            parent_pk = InlineModel.parent_fk()
            esi_pk = InlineModel.esi_pk()
            non_pk_fields = {
                field_name
                for field_name in InlineModel._field_names_not_pk()
                if field_name not in {parent_pk, esi_pk}
            }
            for eve_data_obj in primary_eve_data_obj[inline_field]:
                args = {
                    parent_pk: primary_obj,
                    esi_pk: eve_data_obj[InlineModel.esi_pk()],
                }
                args["defaults"] = {
                    field_name: eve_data_obj[field_name] for field_name in non_pk_fields
                }
                InlineModel.objects.update_or_create(**args)

    def _update_or_create_children_async(self, eve_data_obj: dict) -> None:
        """updates or creates child objects specified in eve mapping"""
        for key, child_class in self.model.child_mappings().items():
            for id in eve_data_obj[key]:
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
