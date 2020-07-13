import logging
from django.core.management.base import BaseCommand

from ... import __title__
from ...tasks import load_map, _eve_object_names_to_be_loaded
from ...utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


def get_input(text):
    """wrapped input to enable unit testing / patching"""
    return input(text)


class Command(BaseCommand):
    help = "Updates Eve Online SDE data"

    def handle(self, *args, **options):
        self.stdout.write("Eve Universe Map Loader")
        self.stdout.write("")
        self.stdout.write(
            "This command will start loading the entire Eve Universe map with "
            "regions, constellations and solar systems from ESI and store it locally. "
        )
        self.stdout.write(
            f"It will also load the following additional entities related to "
            f"the the above mentioned entities: "
            f"{','.join(_eve_object_names_to_be_loaded())}",
        )
        self.stdout.write(
            "Note that this process can take a while to complete "
            "and may cause some significant load to your system."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            self.stdout.write("Starting update. Please stand by.")
            load_map.delay()
            self.stdout.write(self.style.SUCCESS("Load started!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
