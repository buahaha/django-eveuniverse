import logging

from esi.clients import EsiClientProvider

from . import __title__, __version__
from .utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)
esi = EsiClientProvider(app_info_text=f"django-eveuniverse v{__version__}")
