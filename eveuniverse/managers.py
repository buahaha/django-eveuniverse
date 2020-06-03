from pydoc import locate

from django.db import models

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .providers import esi
from .tasks import load_eve_entity
from .utils import LoggerAddTag, make_logger_prefix


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverseManager(models.Manager):

    def get_or_create_esi(self, eve_id: int) -> tuple:
        """gets or creates eve universe object fetched from ESI if needed. 
        Will always get/create parent objects.
        
        eve_id: Eve Online ID of object

        Returns: object, created        
        """
        try:
            obj = self.get(id=eve_id)
            created = False        
        except self.model.DoesNotExist:
            obj, created = self.update_or_create_esi(eve_id)

        return obj, created

    def update_or_create_esi(self, eve_id: int) -> tuple:
        """updates or creates Eve Universe object with data fetched from ESI. 
        Will always update/create children and get/create parent objects.

        eve_id: Eve Online ID of object

        Returns: object, created
        """        
        add_prefix = make_logger_prefix(
            '%s(id=%d)' % (self.model.__name__, eve_id)
        )        
        try:            
            args = {self.model.esi_pk(): eve_id}
            eve_data_obj = (
                getattr(esi.client.Universe, self.model.esi_method())(**args).results()
            )
            defaults = self.model.map_esi_fields_to_model(eve_data_obj)
            obj, created = self.update_or_create(id=eve_id, defaults=defaults)
            obj.save()
            self._update_or_create_children_async(eve_data_obj)
        
        except Exception as ex:
            logger.warn(add_prefix('Failed to update or create: %s' % ex))
            raise ex

        return obj, created

    def _update_or_create_children_async(self, eve_data_obj: dict) -> None:
        """updates or creates child objects specified in eve mapping"""
        for key, child_class in self.model.child_mappings().items():            
            for eve_id in eve_data_obj[key]:                
                load_eve_entity.delay(child_class, eve_id)
