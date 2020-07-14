from celery import shared_task

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

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


logger = LoggerAddTag(get_extension_logger(__name__), __title__)
# logging.getLogger("esi").setLevel(logging.INFO)


@shared_task(base=QueueOnce)
def load_eve_object(
    model_name: str, id: int, include_children=False, wait_for_children=True
) -> None:
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


@shared_task(base=QueueOnce)
def load_map() -> None:
    logger.info(
        "Loading map with regions, constellations, solarsystems "
        "and the following additional entities if related to the map: %s",
        ", ".join(_eve_object_names_to_be_loaded()),
    )
    category, method = models.EveRegion.esi_path_list()
    all_ids = getattr(getattr(esi.client, category), method)().results()
    for id in all_ids:
        load_eve_object.delay(
            model_name="EveRegion",
            id=id,
            include_children=True,
            wait_for_children=False,
        )
