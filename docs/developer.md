# Developer Guide

## Examples

Using the eve models in your own project is straightforward. The syntax is similar to the standard manager methods for Django modes.

Here is an example:

```python
from eveuniverse.models import EveSolarSystem

# get the Jita solar system and load it ad-hoc if needed
jita, _ = EveSolarSystem.objects.get_or_create_esi(id=30000142)

# this will output True
print(jita.is_high_sec)

# this will output the name of it's constellation: Kimotoro
print(jita.eve_constellation.name)
```

## Test data

django-eveuniverse comes with tools that help you generate and use test data for your own apps.

### Generate test data

To generate your test data create a script within your projects and run that scrip as a Django test. That is important to ensure that the database on which the scripts operates is empty. That script will then create a JSON file that contains freshly retrieved Eve objects from ESI based on your specification.

#### create_eveuniverse.py

Here is an example script for generating test data (taken from aa-killtracker):

```Python
from django.test import TestCase

from eveuniverse.tools.testdata import create_testdata, ModelSpec

from . import test_data_filename


class CreateEveUniverseTestData(TestCase):
    def test_create_testdata(self):
        testdata_spec = {
            "EveFaction": ModelSpec(ids=[500001], include_children=False),
            "EveType": ModelSpec(
                ids=[603, 621, 638, 2488, 2977, 3756, 11379, 16238, 34562, 37483],
                include_children=False,
            ),
            "EveSolarSystem": ModelSpec(
                ids=[30001161, 30004976, 30004984, 30045349, 31000005],
                include_children=False,
            ),
            "EveRegion": ModelSpec(ids=[10000038], include_children=True,),
        }
        create_testdata(testdata_spec, test_data_filename())

```

### Using generated testdata in your tests

To user the generated testdata file in your test you need another script that creates objects from your generated JSON file.

#### load_eveuniverse.py

Here is an example script that creates objects from the JSON file.

```Python
import json

from eveuniverse.tools.testdata import load_testdata_from_dict

from . import test_data_filename


def _load_eveuniverse_from_file():
    with open(test_data_filename(), "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


eveuniverse_testdata = _load_eveuniverse_from_file()


def load_eveuniverse():
    load_testdata_from_dict(eveuniverse_testdata)

```

You can then load all Eve objects in your own test script like so:

#### test_example.py

```Python
from django.test import TestCase
from .load_eveuniverse import load_eveuniverse

class MyTest(TestCase):

  @classmethod
  def setUpClass(cls):
      super().setUpClass()
      load_eveuniverse()

  def test_my_test(self):
    svipul = EveType.objects.get(id=34562)
    # ...
```

## Preloading data

While all models support loading eve objects on demand from ESI, some apps might need specific data sets to be preloaded. For example an app might want to provide a drop down list of all structure types, and loading that list on demand would not be fast enough to guarantee acceptable UI response times.

The solution is to provide the user with a management command, so he an preload the needed data sets - for example all ship types - during app installation. Since this is a command use case django-eveuniverse offers a management helper command with all the needed functionality for loading data and which can be easily utilized with just a very small and simple management command ine the app.

Here is an example for creating such a management command in the app. We want to load all kinds of structures to show to the user in a drop down list. We therefore want to preload all structure types (category_id = 65), all control towers (group_id = 365) and the customs office (type_id = 2233):

```Python
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Preloads data required for this app from ESI"

    def handle(self, *args, **options):
        call_command(
            "eveuniverse_load_types",
            __title__,
            "--category_id",
            "65",
            "--group_id",
            "365",
            "--type_id",
            "2233",
        )
```

For more details on how to use `eveuniverse_load_types` just call it with `--help` from a console.
