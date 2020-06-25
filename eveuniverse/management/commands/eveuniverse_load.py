import logging
from django.core.management.base import BaseCommand

from ... import __title__
from ...app_settings import (
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
from ...providers import esi
from ...tasks import load_eve_entity
from ...utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


def get_input(text):
    """wrapped input to enable unit testing / patching"""
    return input(text)


class Command(BaseCommand):
    help = "Updates Eve Online SDE data"

    def _load_models(self):
        self._load_parent("EveRegion", "get_universe_regions")

    def _load_parent(self, model_name, eve_method):
        all_ids = getattr(esi.client.Universe, eve_method)().results()
        counter = 0
        for entity_id in all_ids:
            progress = int(counter / len(all_ids) * 100)
            self.stdout.write(
                f"Loading {model_name} with children "
                f"for ID {entity_id} ({progress}% complete)"
            )
            result = load_eve_entity.apply_async(
                kwargs={
                    "model_name": model_name,
                    "entity_id": entity_id,
                    "include_children": True,
                    "wait_for_children": False,
                }
            )
            result.get()
            counter += 1

    def handle(self, *args, **options):
        self.stdout.write("Eve Universe Loader")
        self.stdout.write("")
        self.stdout.write("Here is the current load configuration:")
        self.stdout.write(f"Load asteroid belts: {EVEUNIVERSE_LOAD_ASTEROID_BELTS}")
        self.stdout.write(f"Load dogmas: {EVEUNIVERSE_LOAD_DOGMAS}")
        self.stdout.write(f"Load graphics: {EVEUNIVERSE_LOAD_GRAPHICS}")
        self.stdout.write(f"Load market groups: {EVEUNIVERSE_LOAD_MARKET_GROUPS}")
        self.stdout.write(f"Load moons: {EVEUNIVERSE_LOAD_MOONS}")
        self.stdout.write(f"Load planets: {EVEUNIVERSE_LOAD_PLANETS}")
        self.stdout.write(f"Load stargates: {EVEUNIVERSE_LOAD_STARGATES}")
        self.stdout.write(f"Load stars: {EVEUNIVERSE_LOAD_STARS}")
        self.stdout.write(f"Load stations: {EVEUNIVERSE_LOAD_STATIONS}")
        self.stdout.write("")
        self.stdout.write(
            "This command will load the complete Eve Universe from ESI and "
            "store it locally. This process can take a long time to complete."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            self.stdout.write("Starting update. Please stand by.")
            self._load_models()
            self.stdout.write(self.style.SUCCESS("Update completed!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
