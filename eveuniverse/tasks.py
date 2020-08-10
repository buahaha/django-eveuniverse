import logging
from typing import List

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
)
from .models import EveUniverseEntityModel
from .providers import esi
from .utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)
# logging.getLogger("esi").setLevel(logging.INFO)

EVE_CATEGORY_ID_SHIP = 6
EVE_CATEGORY_ID_STRUCTURE = 65


@shared_task
def load_eve_object(
    model_name: str, id: int, include_children=False, wait_for_children=True
) -> None:
    """Task for loading an eve object. 
    Will only be created from ESI if it does not exist
    """
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.get_or_create_esi(
        id=id, include_children=include_children, wait_for_children=wait_for_children
    )


@shared_task
def update_or_create_eve_object(
    model_name: str, id: int, include_children=False, wait_for_children=True
) -> None:
    """Task for updating or creating an eve object from ESI"""
    ModelClass = EveUniverseEntityModel.get_model_class(model_name)
    ModelClass.objects.update_or_create_esi(
        id=id, include_children=include_children, wait_for_children=wait_for_children,
    )


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


@shared_task
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


def _load_category(category_id: int) -> None:
    """Starts a task for loading a category incl. all it's children from ESI via"""
    update_or_create_eve_object.delay(
        model_name="EveCategory",
        id=category_id,
        include_children=True,
        wait_for_children=False,
    )


def _load_group(group_id: int) -> None:
    """Starts a task for loading a group incl. all it's children from ESI"""
    update_or_create_eve_object.delay(
        model_name="EveGroup",
        id=group_id,
        include_children=True,
        wait_for_children=False,
    )


def _load_type(type_id: int) -> None:
    """Starts a task for loading a type incl. all it's children from ESI"""
    update_or_create_eve_object.delay(
        model_name="EveType",
        id=type_id,
        include_children=True,
        wait_for_children=False,
    )


@shared_task
def load_ship_types() -> None:
    """Loads all ship types"""
    logger.info("Started loading all ship types into eveuniverse")
    _load_category(EVE_CATEGORY_ID_SHIP)


@shared_task
def load_structure_types() -> None:
    """Loads all structure types"""
    logger.info("Started loading all structure types into eveuniverse")
    _load_category(EVE_CATEGORY_ID_STRUCTURE)


@shared_task
def load_eve_types(
    category_ids: List[int] = None,
    group_ids: List[int] = None,
    type_ids: List[int] = None,
) -> None:
    """Load specified eve types from ESI. Will always load all children"""
    logger.info("Started loading several eve types into eveuniverse")
    if category_ids:
        for category_id in category_ids:
            _load_category(category_id)

    if group_ids:
        for group_id in group_ids:
            _load_group(group_id)

    if type_ids:
        for type_id in type_ids:
            _load_type(type_id)
