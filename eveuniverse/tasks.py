import logging
from typing import List, Iterable

from celery import shared_task

from . import __title__
from . import models
from .app_settings import (
    EVEUNIVERSE_LOAD_DOGMAS,
    EVEUNIVERSE_LOAD_MARKET_GROUPS,
    EVEUNIVERSE_LOAD_ASTEROID_BELTS,
    EVEUNIVERSE_LOAD_GRAPHICS,
    EVEUNIVERSE_LOAD_MOONS,
    EVEUNIVERSE_LOAD_PLANETS,
    EVEUNIVERSE_LOAD_STARGATES,
    EVEUNIVERSE_LOAD_STARS,
    EVEUNIVERSE_LOAD_STATIONS,
    EVEUNIVERSE_TASKS_TIME_LIMIT,
)
from .models import EveUniverseEntityModel, EveEntity, EveMarketPrice
from .providers import esi
from .utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)
# logging.getLogger("esi").setLevel(logging.INFO)

EVE_CATEGORY_ID_SHIP = 6
EVE_CATEGORY_ID_STRUCTURE = 65


# Eve Universe objects


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def load_eve_object(
    model_name: str, id: int, include_children=False, wait_for_children=True
) -> None:
    """Task for loading an eve object.
    Will only be created from ESI if it does not exist
    """
    logger.info("Loading %s with ID %s", model_name, id)
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.get_or_create_esi(
        id=id, include_children=include_children, wait_for_children=wait_for_children
    )


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def update_or_create_eve_object(
    model_name: str,
    id: int,
    include_children=False,
    wait_for_children=True,
    enabled_sections: List[str] = None,
) -> None:
    """Task for updating or creating an eve object from ESI"""
    logger.info("Updating/Creating %s with ID %s", model_name, id)
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(
        id=id,
        include_children=include_children,
        wait_for_children=wait_for_children,
        enabled_sections=enabled_sections,
    )


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def update_or_create_inline_object(
    parent_obj_id: int,
    parent_fk: str,
    eve_data_obj: dict,
    other_pk_info: dict,
    parent2_model_name: str,
    inline_model_name: str,
    parent_model_name: str,
) -> None:
    """Task for updating or creating a single inline object from ESI"""
    logger.info(
        "Updating/Creating inline object %s for %s wit ID %s",
        inline_model_name,
        parent_model_name,
        parent_obj_id,
    )
    ModelClass = EveUniverseEntityModel.get_model_class(parent_model_name)
    ModelClass.objects._update_or_create_inline_object(
        parent_obj_id=parent_obj_id,
        parent_fk=parent_fk,
        eve_data_obj=eve_data_obj,
        other_pk_info=other_pk_info,
        parent2_model_name=parent2_model_name,
        inline_model_name=inline_model_name,
    )


# EveEntity objects


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def create_eve_entities(ids: Iterable[int]) -> None:
    """Task for bulk creating and resolving multiple entities from ESI."""
    EveEntity.objects.bulk_create_esi(ids)


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def update_unresolved_eve_entities() -> None:
    """Task for bulk updating all unresolved EveEntity objects in the database from ESI."""
    EveEntity.objects.bulk_update_new_esi()


# Object loaders


def _eve_object_names_to_be_loaded() -> list:
    """returns a list of eve object that are loaded"""
    config_map = [
        (EVEUNIVERSE_LOAD_DOGMAS, "dogmas"),
        (EVEUNIVERSE_LOAD_MARKET_GROUPS, "market groups"),
        (EVEUNIVERSE_LOAD_ASTEROID_BELTS, "asteroid belts"),
        (EVEUNIVERSE_LOAD_GRAPHICS, "graphics"),
        (EVEUNIVERSE_LOAD_MOONS, "moons"),
        (EVEUNIVERSE_LOAD_PLANETS, "planets"),
        (EVEUNIVERSE_LOAD_STARGATES, "stargates"),
        (EVEUNIVERSE_LOAD_STARS, "stars"),
        (EVEUNIVERSE_LOAD_STATIONS, "stations"),
    ]
    names_to_be_loaded = []
    for setting, entity_name in config_map:
        if setting:
            names_to_be_loaded.append(entity_name)
    return sorted(names_to_be_loaded)


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def load_map() -> None:
    """loads the complete Eve map with all regions, constellation and solarsystems
    and additional related entities if they are enabled
    """
    logger.info(
        "Loading complete map with all regions, constellations, solarsystems "
        "and the following additional entities if related to the map: %s",
        ", ".join(_eve_object_names_to_be_loaded()),
    )
    category, method = models.EveRegion._esi_path_list()
    all_ids = getattr(getattr(esi.client, category), method)().results()
    for id in all_ids:
        update_or_create_eve_object.delay(
            model_name="EveRegion",
            id=id,
            include_children=True,
            wait_for_children=False,
        )


def _load_category(category_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a category incl. all it's children from ESI via"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveCategory",
        id=category_id,
        include_children=True,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


def _load_group(group_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a group incl. all it's children from ESI"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveGroup",
        id=group_id,
        include_children=True,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


def _load_type(type_id: int, force_loading_dogma: bool = False) -> None:
    """Starts a task for loading a type incl. all it's children from ESI"""
    enabled_sections = (
        [EveUniverseEntityModel.LOAD_DOGMAS] if force_loading_dogma else None
    )
    update_or_create_eve_object.delay(
        model_name="EveType",
        id=type_id,
        include_children=False,
        wait_for_children=False,
        enabled_sections=enabled_sections,
    )


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def load_ship_types() -> None:
    """Loads all ship types"""
    logger.info("Started loading all ship types into eveuniverse")
    _load_category(EVE_CATEGORY_ID_SHIP)


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def load_structure_types() -> None:
    """Loads all structure types"""
    logger.info("Started loading all structure types into eveuniverse")
    _load_category(EVE_CATEGORY_ID_STRUCTURE)


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def load_eve_types(
    category_ids: List[int] = None,
    group_ids: List[int] = None,
    type_ids: List[int] = None,
    force_loading_dogma: bool = False,
) -> None:
    """Load specified eve types from ESI. Will always load all children except for EveType

    Args:
    - category_ids: EveCategory IDs
    - group_ids: EveGroup IDs
    - type_ids: EveType IDs
    - load_dogma: When True will load dogma for all types
    """
    logger.info("Started loading several eve types into eveuniverse")
    if category_ids:
        for category_id in category_ids:
            _load_category(category_id, force_loading_dogma)

    if group_ids:
        for group_id in group_ids:
            _load_group(group_id, force_loading_dogma)

    if type_ids:
        for type_id in type_ids:
            _load_type(type_id, force_loading_dogma)


@shared_task(time_limit=EVEUNIVERSE_TASKS_TIME_LIMIT)
def update_market_prices(minutes_until_stale: int = None):
    """Updates market prices from ESI.
    see EveMarketPrice.objects.update_from_esi() for details"""
    EveMarketPrice.objects.update_from_esi(minutes_until_stale)
