import logging
from django.core.management.base import BaseCommand

from ... import __title__
from ...tasks import (
    load_map,
    load_ship_types,
    load_structure_types,
    _eve_object_names_to_be_loaded,
)
from ...utils import LoggerAddTag
from . import get_input


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


class Command(BaseCommand):
    help = "Loads large sets of data from ESI into local database"

    def add_arguments(self, parser):
        parser.add_argument("area", choices=["map", "ships", "structures"])

    def handle(self, *args, **options):
        self.stdout.write("Eve Universe - Data Loader - A")
        self.stdout.write("")

        if options["area"] == "map":
            text = (
                "This command will start loading the entire Eve Universe map with "
                "regions, constellations and solar systems from ESI and store it "
                "locally. "
            )
            my_task = load_map

        elif options["area"] == "ships":
            text = "This command will load all ship types from ESI."
            my_task = load_ship_types

        elif options["area"] == "structures":
            text = "This command will load all structure types from ESI."
            my_task = load_structure_types

        else:
            raise RuntimeError("This exception should be unreachable")

        self.stdout.write(text)

        self.stdout.write(
            "It will also load the following additional entities when related to "
            "the above mentioned entities: "
            f"{','.join(_eve_object_names_to_be_loaded())}"
        )
        self.stdout.write(
            "Note that this process can take a while to complete "
            "and may cause some significant load to your system."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            self.stdout.write("Starting update. Please stand by.")
            my_task.delay()
            self.stdout.write(self.style.SUCCESS("Load started!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
