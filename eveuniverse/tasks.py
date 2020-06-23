# import logging

from celery import shared_task

from allianceauth.services.hooks import get_extension_logger

from . import __title__
from . import models
from .providers import esi
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)
# logging.getLogger("esi").setLevel(logging.INFO)


def _get_model_class(model_name: str) -> object:
    if not hasattr(models, model_name):
        raise ValueError("Unknown model_name: %s" % model_name)

    return getattr(models, model_name)


@shared_task
def load_eve_entity(model_name: str, entity_id: int) -> None:
    ModelClass = _get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(
        entity_id, include_children=True, wait_for_children=False
    )


@shared_task(ignore_result=False)
def load_eve_entities_bulk(
    model_name: str, esi_path: str, eve_ids: list = None
) -> None:
    all_ids = set(getattr(esi.client.Universe, esi_path)().results())
    if eve_ids is not None:
        requested_ids = all_ids.subset(set(eve_ids))
    else:
        requested_ids = all_ids

    for entity_id in requested_ids:
        load_eve_entity.delay(model_name, entity_id)


@shared_task
def load_categories(eve_ids: list = None) -> None:
    load_eve_entities_bulk("EveCategory", "get_universe_categories", eve_ids)


@shared_task
def load_groups(eve_ids: list = None) -> None:
    load_eve_entities_bulk("EveGroup", "get_universe_groups", eve_ids)


@shared_task
def load_types(eve_ids: list = None) -> None:
    load_eve_entities_bulk("EveType", "get_universe_types", eve_ids)
