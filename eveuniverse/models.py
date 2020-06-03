from django.db import models
from django.utils.timezone import now

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from .managers import EveUniverseManager
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class EveUniverse(models.Model):

    id = models.PositiveIntegerField(
        primary_key=True, help_text='Eve Online ID'
    )
    name = models.CharField(
        max_length=100, help_text='Eve Online name'
    )    
    last_updated = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        help_text='When this object was last updated from ESI',
        db_index=True
    )

    objects = EveUniverseManager()

    class Meta:
        abstract = True

    def __repr__(self):
        return '{}(id={}, name=\'{}\')'.format(
            self.__class__.__name__,
            self.id,
            self.name
        )

    def __str__(self):
        return self.name

    @classmethod
    def esi_pk(cls) -> str:
        """returns the name of the pk column on ESI that must exist"""
        return cls._eve_universe_meta_attr('esi_pk', is_mandatory=True)
       
    @classmethod
    def esi_method(cls) -> str:        
        return cls._eve_universe_meta_attr('esi_method', is_mandatory=True)

    @classmethod
    def map_esi_fields_to_model(cls, eve_data_obj: dict) -> dict:
        """maps ESi fields to model fields incl. translations if any
        returns the result as defaults dict
        """
        fk_mappings = cls._fk_mappings()
        field_mappings = cls._field_mappings()                        
        defaults = {'last_updated': now()}        
        for key in cls._field_names_not_pk():
            if key in fk_mappings:
                esi_key, ParentClass = fk_mappings[key]                    
                value, _ = ParentClass.objects.get_or_create_esi(
                    eve_data_obj[esi_key]
                )                
            else:
                if key in field_mappings:
                    mapping = field_mappings[key]
                    if len(mapping) != 2:
                        raise ValueError(
                            'Currently only supports mapping to 1-level '
                            'nested dicts'
                        )
                    value = eve_data_obj[mapping[0]][mapping[1]]
                else:
                    value = eve_data_obj[key]

            defaults[key] = value
        
        return defaults

    @classmethod
    def _field_mappings(cls) -> dict:
        """returns the mappings for model fields vs. esi fields"""        
        mappings = cls._eve_universe_meta_attr('field_mappings')
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
                esi_name = name.replace('eve_', '') + '_id'
            return esi_name
        
        extra_fk_mappings = cls._eve_universe_meta_attr('fk_mappings')
        if not extra_fk_mappings:
            extra_fk_mappings = {}

        mappings = {
            x.name: (
                convert_to_esi_name(x.name, extra_fk_mappings), 
                x.related_model
            )
            for x in cls._meta.get_fields() 
            if isinstance(x, models.ForeignKey)
        }
        return mappings

    @classmethod
    def _field_names_not_pk(cls) -> set:
        """returns field names excl. PK, localization and auto created fields"""
        return {
            x.name for x in cls._meta.get_fields()
            if not x.auto_created and (
                not hasattr(x, 'primary_key') or x.primary_key is False
            ) and x.name not in {'language_code', 'last_updated'}
            and 'name_' not in x.name
        }

    @classmethod
    def _eve_universe_meta_attr(
        cls, attr_name: str, is_mandatory: bool = False
    ):
        """returns value of an attribute from EveUniverseMeta or None"""
        if not hasattr(cls, 'EveUniverseMeta'):
            raise ValueError(
                'EveUniverseMeta not defined for class %s' % cls.__name__
            )
    
        if hasattr(cls.EveUniverseMeta, attr_name):
            value = getattr(cls.EveUniverseMeta, attr_name)
        else:
            value = None
            if is_mandatory:
                raise ValueError(
                    'Mandatory attribute EveUniverseMeta.%s not defined '
                    'for class %s' % (attr_name, cls.__name__)
                )
        return value


class EveCategory(EveUniverse):
    """category in Eve Online"""
    
    class EveUniverseMeta:
        esi_pk = 'category_id'
        esi_method = 'get_universe_categories_category_id'


class EveGroup(EveUniverse):
    """group in Eve Online"""
        
    eve_category = models.ForeignKey(EveCategory, on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = 'group_id'
        esi_method = 'get_universe_groups_group_id'


class EveType(EveUniverse):
    """type in Eve Online"""
    
    eve_group = models.ForeignKey(EveGroup, on_delete=models.CASCADE)

    class EveUniverseMeta:
        esi_pk = 'type_id'
        esi_method = 'get_universe_types_type_id'
