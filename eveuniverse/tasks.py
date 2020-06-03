import concurrent.futures
from functools import partial

from celery import shared_task, chain

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from . import models
from .helpers.esi_fetch import esi_fetch
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)

MAX_WORKER = 10


def _get_model_class(model_name: str) -> object:
    if not hasattr(models, model_name):
        raise ValueError('Unknown model_name: %s' % model_name)
    
    return getattr(models, model_name)


def thread_load_entity(model_name: str, eve_id: int) -> None:    
    ModelClass = _get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(eve_id=eve_id)


def load_all_entities(
    model_name: str, esi_method: str, has_pages: bool = False
) -> None:
    entity_ids = esi_fetch(esi_method, has_pages=has_pages)
    thread_func = partial(thread_load_entity, model_name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
        executor.map(thread_func, entity_ids)


@shared_task
def load_categories() -> None:
    load_all_entities(
        'EveCategory', 'Universe.get_universe_categories', has_pages=False
    )


@shared_task
def load_groups() -> None:
    load_all_entities('EveGroup', 'Universe.get_universe_groups', has_pages=True)


@shared_task
def load_types() -> None:
    load_all_entities('EveType', 'Universe.get_universe_types', has_pages=True)


@shared_task
def load_universe() -> None:
    my_chain = list()
    my_chain.append(load_categories.si())
    my_chain.append(load_groups.si())
    my_chain.append(load_types.si())
    chain(my_chain).delay()
