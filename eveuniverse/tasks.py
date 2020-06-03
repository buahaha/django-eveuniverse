import concurrent.futures
from functools import partial
import logging

from celery import shared_task, chain

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from . import models
from .providers import esi
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)
logging.getLogger('esi').setLevel(logging.INFO)

MAX_WORKER = 50


def _get_model_class(model_name: str) -> object:
    if not hasattr(models, model_name):
        raise ValueError('Unknown model_name: %s' % model_name)
    
    return getattr(models, model_name)


@shared_task
def load_eve_entity(model_name: str, eve_id: int) -> None:    
    ModelClass = _get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(eve_id=eve_id)


def load_all_entities(model_name: str, esi_method: str) -> None:
    entity_ids = getattr(esi.client.Universe, esi_method)().results()
    thread_func = partial(load_eve_entity, model_name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
        executor.map(thread_func, entity_ids)


@shared_task
def load_categories() -> None:
    load_all_entities('EveCategory', 'get_universe_categories')


@shared_task
def load_groups() -> None:
    load_all_entities('EveGroup', 'get_universe_groups')


@shared_task
def load_types() -> None:
    load_all_entities('EveType', 'get_universe_types')


@shared_task
def load_universe() -> None:
    my_chain = list()
    my_chain.append(load_categories.si())
    my_chain.append(load_groups.si())
    my_chain.append(load_types.si())
    chain(my_chain).delay()
