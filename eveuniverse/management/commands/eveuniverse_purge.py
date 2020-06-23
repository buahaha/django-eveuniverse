from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import (
    EveAncestry,
    EveAsteroidBelt,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveDogmaEffectModifier,
    EveFaction,
    EveGroup,
    EveMarketGroup,
    EveMoon,
    EvePlanet,
    EveRace,
    EveRegion,
    EveSolarSystem,
    EveStar,
    EveStargate,
    EveStation,
    EveType,
    EveTypeDogmaAttribute,
    EveTypeDogmaEffect,
)


def get_input(text):
    """wrapped input to enable unit testing / patching"""
    return input(text)


class Command(BaseCommand):
    help = (
        "Removes all app-related data from the database. "
        "Run this command before zero migrations, "
        "which would otherwise fail due to FK constraints."
    )

    def _purge_all_data(self):
        """updates all SDE models from ESI and provides progress output"""
        models = [
            EveCategory,
            EveGroup,
            EveType,
            EveDogmaAttribute,
            EveDogmaEffect,
            EveDogmaEffectModifier,
            EveTypeDogmaEffect,
            EveTypeDogmaAttribute,
            EveRace,
            EvePlanet,
            EveStation,
            EveBloodline,
            EveAncestry,
            EveRegion,
            EveConstellation,
            EveSolarSystem,
            EveAsteroidBelt,
            EveFaction,
            EveMoon,
            EveStar,
            EveStargate,
            EveMarketGroup,
        ]
        with transaction.atomic():
            for MyModel in models:
                self.stdout.write(
                    "Deleting {:,} objects from {}".format(
                        MyModel.objects.count(), MyModel.__name__,
                    )
                )
                MyModel.objects.all().delete()

    def handle(self, *args, **options):
        self.stdout.write(
            "This command will delete all app related data in the database. "
            "This can not be undone. Use with caution."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            self.stdout.write("Starting data purge. Please stand by.")
            self._purge_all_data()
            self.stdout.write(self.style.SUCCESS("Purge complete!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
