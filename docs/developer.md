# Developer Guide

## Basics

*django-eveuniverse* implements Django models for all eve objects from the ESI Universe category plus some related objects. These models can then be used in queries or included as related models in your app's own models.

The name of all models start with `Eve` and then the name of the object class. For example the model for solar systems is called `EveSolarSystem`.

### Properties

All Eve model share the following basic properties:

- `id`: The Eve Online ID of the object and also the primary key
- `name`: The name of the eve objects
- `last_updated`: The date & time this object was last updated from ESI

Properties that reference other Eve models always have the name of the referenced model, just in snake case. e.g. a property references a EveSolarSystem object would be called `eve_solar_system`.

### Magic Methods

All Eve models have the following magic methods implemented:

- `__str__()`: returns the name of an object
- `__repr__()`: returns the complete object with all properties as model instance

### Fetching eve objects

All Eve models support on-demand loading of eve objects from ESI. This functionality is is available through manager methods. One of these methods is `get_or_create_esi()`, which works similar to Django's `get_or_create()` method and will return the requested object along with a boolean flag showing if the object was created or not.

For example for getting the solar system of Jita you could do the following:

```python
>>> EveSolarSystem.objects.get_or_create_esi(id=30000142)
(EveSolarSystem(eve_constellation_id=20000020, eve_star_id=None, id=30000142, name='Jita', position_x=-1.2906486173487826e+17, position_y=6.075530690996363e+16, position_z=1.1746922706009029e+17, security_status=0.9459131360054016), True)
```

Once loaded the object will be automatically stored in the database and the next time the same command would return the local copy.

Sometimes you may want to always fetch a fresh Eve objects from Esi. For that you can call `update_or_create_esi()`, which will always retrieve a new Eve objects and update the local copy.

Our example for Jita would then look like this:

```python
>>> EveSolarSystem.objects.get_or_create_esi(id=30000142)
(EveSolarSystem(eve_constellation_id=20000020, eve_star_id=None, id=30000142, name='Jita', position_x=-1.2906486173487826e+17, position_y=6.075530690996363e+16, position_z=1.1746922706009029e+17, security_status=0.9459131360054016), False)
```

Alternatively, a set of eve objects can be preloaded, e.g. during installation of an app, so the app can later rely those eve objects to already be in the database. For details please see [Preloading data](#preloading-data)

### Fetching parent and child objects

Most Eve models have relations with both parent and child models. When fetching an Eve objects for the first time from ESI, the related parent objects will automatically be loaded too to ensure the integrity of the database. For example if you are fetching Jita for the first time, the objects for Jita's constellation (parent of solar system) and Jita's region (parent of constellation) will be fetched too.

In addition it is possible to automatically fetch all children of an object. This can be vry useful for loading larger sets of data. For example if you want to load all ship types, you can just fetch the inventory category for ships with all it's children. (Please see the method's API for more details.)

### Selecting which models are loaded

Eve models are heavily interrelated and trying to load just a small subset of objects can quickly cascade to loading large parts of the whole universe. However, not all of those related models are needed by every app and always loading them would only increase overall response times without any real benefit.

For example the dogma consists of 4 models that relate to inventory types and contain specifics for type objects like the rate of fire for some ship modules. Not every app may need that additional information in their database.

Our solution is to offer developers control over which models are loaded and which are not through settings. By default the following eve models are not loaded automatically and need to be turned on explicitly (see also Settings for details):

- EveAsteroidBelt
- EveDogmaAttribute
- EveDogmaEffect
- EveGraphic
- EveMarketGroup
- EveMoon
- EvePlanet
- EveStargate
- EveStar
- EveStation

```eval_rst
.. note::
    You can still load objects from disabled models directly - e.g. with get_or_create_esi() - but be mindful that relations will not be created automatically, which can lead to inconsistencies in your database.
```

```eval_rst
.. hint::
    When turning on models you usually will want to reload your related eve objects to make sure all relations are created correctly. e.g. after turning on "EveStargate" you want to reload the map, so that all stargates are loaded.
```

### Additional functionality

Some Eve models provide additional useful functionality, e.g. icon image URLs. Especially `EveSolarSystem` comes with a lot of additional features incl. a route finder. Please see the API for details.

### Name resolution

A common problem when working with data from ESI is the need to resolve IDs to names / objects. To make this easier *django-eveuniverse* provides a dedicated model called `EveEntity`. `EveEntity` allows you to quickly resolve large amounts of IDs to objects, which include their respective names and categories in bulk. Resolved objects are automatically stored locally and used to speed up subsequent ID resolving.

Here is a simple example for resolving one ID:

```python
>>> EveEntity.objects.resolve_name(30000142)
'Jita'
```

This examples show how to resolve a list of IDs in bulk and using a resolver object to access the results:

```python
>>> resolver = EveEntity.objects.bulk_resolve_names([30000142, 34562, 498125261])
>>> resolver.to_name(30000142)
'Jita'
>>> resolver.to_name(34562)
'Svipul'
>>> resolver.to_name(498125261)
'Svipul'
>>> resolver.to_name(498125261)
'Test Alliance Please Ignore'
```

Another approach is to bulk create EveEntity objects with the ID only and then resolve all "new" objects with `EveEntity.objects.bulk_update_new_esi()`. This approach works well when using EveEntity objects as property in you app's models.

For more features and details please see the API of `EveEntity`.

## Test data

*django-eveuniverse* comes with tools that help you generate and use test data for your own apps.

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

The solution is to provide the user with a management command, so he an preload the needed data sets - for example all ship types - during app installation. Since this is a command use case *django-eveuniverse* offers a management helper command with all the needed functionality for loading data and which can be easily utilized with just a very small and simple management command ine the app.

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
