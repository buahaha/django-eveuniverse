import csv
from bz2 import decompress
from datetime import datetime
from email.utils import mktime_tz, parsedate_tz
import inspect
import logging
import json
import os

import pytz
import requests

from django.core.management.base import BaseCommand

from ... import __title__
from ...utils import LoggerAddTag


logger = LoggerAddTag(logging.getLogger(__name__), __title__)

DOWNLOAD_SERVER_BASE_URL = "https://www.fuzzwork.co.uk/dump/latest/"
_currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def get_input(text):
    """wrapped input to enable unit testing / patching"""
    return input(text)


class Command(BaseCommand):
    help = "Updates Eve Online SDE data"

    def _fetch_sde_table_from_server(self, table_name: str) -> list:
        """Returns an SDE table from the download server as list of dicts """

        # fetch the file from the FTP server
        logger.info("Fetching table %s from download server...", table_name)
        response = requests.get(DOWNLOAD_SERVER_BASE_URL + table_name + ".csv.bz2")
        response.raise_for_status()

        # get date
        timestamp = mktime_tz(parsedate_tz(response.headers["last-modified"]))
        utc_dt = datetime.utcfromtimestamp(timestamp)
        version = pytz.utc.localize(utc_dt)

        # decompress data and convert to CSV list
        file_bz2 = response.content
        csv_list = decompress(file_bz2).decode("utf-8").splitlines()

        # return rows as list of dicts
        rows = list(csv.DictReader(csv_list, delimiter=","))
        logger.info("Loaded table %s from download server", table_name)
        return version, rows

    def _fetch_sde(self):
        version, rows = self._fetch_sde_table_from_server("eveUnits")
        migrations_folder = os.path.join(
            os.path.dirname(os.path.dirname(_currentdir)), "migrations"
        )
        path = f"{migrations_folder}/eve_unit.json"
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(rows, f)

        self.stdout.write("EveUnit data file create at: %s" % path)

    def handle(self, *args, **options):
        self.stdout.write(
            "This command will fetch missing SDE data (e.g. eveUnits) "
            "from fuzzworks FTP and store them as JSON into the migrations folder."
        )
        user_input = get_input("Are you sure you want to proceed? (Y/n)?")
        if user_input == "Y":
            self.stdout.write("Starting update. Please stand by.")
            self._fetch_sde()
            self.stdout.write(self.style.SUCCESS("Process completed!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted"))
