import logging
from django.core.management.base import BaseCommand

from ... import __title__
from ...tasks import load_eve_types, _eve_object_names_to_be_loaded
from ...utils import LoggerAddTag
from . import get_input


logger = LoggerAddTag(logging.getLogger(__name__), __title__)


class Command(BaseCommand):
    help = (
        "Loads large sets of types as specified from ESI into the local database."
        " This is a helper command meant to be called from other apps only."
    )

    def add_arguments(self, parser):
        parser.add_argument("app_name", help="Name of app this data is loaded for")
        parser.add_argument(
            "--category_id",
            action="append",
            type=int,
            help="Eve category ID to be loaded",
        )
        parser.add_argument(
            "--group_id", action="append", type=int, help="Eve group ID to be loaded"
        )
        parser.add_argument(
            "--type_id", action="append", type=int, help="Eve type ID to be loaded"
        )

    def handle(self, *args, **options):
        app_name = options["app_name"]
        category_ids = options["category_id"]
        group_ids = options["group_id"]
        type_ids = options["type_id"]

        if not category_ids and not group_ids and not type_ids:
            self.stdout.write(self.style.WARNING("No IDs specified. Nothing to do."))
            return

        self.stdout.write("Eve Universe - Types Loader")
        self.stdout.write("===========================")
        self.stdout.write(
            f"This command will start loading data for the app: {app_name}."
        )
        additional_objects = _eve_object_names_to_be_loaded()
        if additional_objects:
            self.stdout.write(
                "It will also load the following additional entities when related to "
                "objects loaded for the app: "
                f"{','.join(additional_objects)}"
            )
        self.stdout.write(
            "Note that this process can take a while to complete "
            "and may cause some significant load to your system."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            load_eve_types.delay(
                category_ids=category_ids, group_ids=group_ids, type_ids=type_ids
            )
            self.stdout.write(self.style.SUCCESS("Data loading has been started!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))