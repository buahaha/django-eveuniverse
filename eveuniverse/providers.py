import logging

from esi.clients import EsiClientProvider

from . import __title__
from .utils import LoggerAddTag, get_swagger_spec_path


logger = LoggerAddTag(logging.getLogger(__name__), __title__)
esi = EsiClientProvider(spec_file=get_swagger_spec_path())
