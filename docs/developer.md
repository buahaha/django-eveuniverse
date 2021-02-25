# Developer Guide

The developer guide describes how to develop apps with *django-eveuniverse*.

## Models

*django-eveuniverse* provides you with ready-made Django models for all Eve Universe classes. These models can be used like any other Django model in queries or included as related models in your app's own models.

```eval_rst
.. note::
    The "Eve Universe" classes are the classes from the Universe category in ESI plus the related classes for dogma and market groups. The objects of those classes change rarely and most changes are just adding new objects (e.g. new types). They are therefore well suited to be stored and cached locally for a longer period of time.

    The Eve Universe classes consist mostly of the same objects as the `Static Data Export <https://wiki.eveuniversity.org/Static_Data_Export>`_ (SDE).
```

```eval_rst
.. seealso::
    Please see :ref:`api-eve-models` for the full documentation of all available models.
```

### Relationship diagram

The following graph shows all models and how they are interrelated:

```eval_rst
    .. image::  _static/images/aa-eveuniverse_models.png
        :target: _static/images/aa-eveuniverse_models.png
```

### Naming of models and properties

The name of all models start with `Eve`. For example the model for solar systems is called `EveSolarSystem`.

All Eve model share the following basic properties:

- `id`: The Eve Online ID of the object and also the primary key
- `name`: The name of the eve objects
- `last_updated`: The date & time this object was last updated from ESI

Property names are mostly the same as in the ESI specification. The exceptions are:

- The common properties `id` and `name` as described above
- Boolean fields start with `is_`
- Properties that reference other Eve models always have the name of the referenced model, just in snake case. e.g. a property references a EveSolarSystem object would be called `eve_solar_system`.

### Magic Methods

All Eve models have the following magic methods implemented:

- `__str__()`: returns the name of an object
- `__repr__()`: returns the complete object with all properties as model instance.

Examples:

```Python
>>> str(EveSolarSystem.objects.get(id=30000142))
'Jita'
```

```Python
>>> repr(EveSolarSystem.objects.get(id=30000142))
"EveSolarSystem(eve_constellation_id=20000020, eve_star_id=None, id=30000142, name='Jita', position_x=-1.2906486173487826e+17, position_y=6.075530690996363e+16, position_z=1.1746922706009029e+17, security_status=0.9459131360054016)"
```

### Additional functionality in Eve Models

Some Eve models provide additional useful functionality, e.g. icon image URLs.

For example the `EveSolarSystem` comes with a lot of additional features incl. a route finder:

```Python
>>> jita = EveSolarSystem.objects.get(id=30000142)
>>> akidagi = EveSolarSystem.objects.get(id=30045342)
>>> jita.jumps_to(akidagi)
10
```

## Fetching eve objects from ESI

### Fetching eve objects on-demand

To fetch an eve object you can simply call it's manager method `get_or_create_esi()`. This will return the requested eve objects from the database if it exists, or else automatically load it from ESI:

For example for getting the solar system of Jita on-demand you could do the following:

```python
>>> EveSolarSystem.objects.get_or_create_esi(id=30000142)
(EveSolarSystem(eve_constellation_id=20000020, eve_star_id=None, id=30000142, name='Jita', position_x=-1.2906486173487826e+17, position_y=6.075530690996363e+16, position_z=1.1746922706009029e+17, security_status=0.9459131360054016), True)
```

Or if want to fetch a fresh Eve object from ESI you can call the manager method `update_or_create_esi()`. This which will always retrieve a new Eve objects from ESI and update the local copy.

Our example for Jita would then look like this:

```python
>>> EveSolarSystem.objects.get_or_create_esi(id=30000142)
(EveSolarSystem(eve_constellation_id=20000020, eve_star_id=None, id=30000142, name='Jita', position_x=-1.2906486173487826e+17, position_y=6.075530690996363e+16, position_z=1.1746922706009029e+17, security_status=0.9459131360054016), False)
```

```eval_rst
.. hint::
    Please see :ref:`api-manager-methods` for an overview of all available methods.
```

### Fetching parent and child objects

Many Eve models have parent and child models. For example `EveSolarSystem` has `EveConstellation` as parent model, and `EvePlanet` is one of its child models. When fetching an Eve objects for the first time from ESI, the related parent objects will automatically be loaded to preserve the integrity of the database.

For example if you are fetching Jita for the first time, the objects for Jita's constellation (parent of solar system) and Jita's region (parent of constellation) will be fetched too.

In addition it is possible to automatically fetch all children of an object. This can be very useful for loading larger sets of data. For example, if you want to load all ship types, you can just fetch the inventory category for ships and include children by setting `include_children` to `True`.

Example:

```python
>>> EveCategory.objects.get_or_create_esi(id=6, include_children=True)
(EveCategory(id=6, name='Ship', published=True), False)
```

This will load all children blocking, which can take quite some time. For large sets of data it is often is better to load children async (via Celery). This can be done by setting `wait_for_children` to `False`.

```python
>>> EveCategory.objects.get_or_create_esi(id=6, include_children=True, wait_for_children=False)
(EveCategory(id=6, name='Ship', published=True), False)
```

### Selecting which related models are loaded

Eve models are heavily interrelated and trying to load just a small subset of objects can quickly cascade to loading large parts of the whole universe. However, not all of those related models are needed by every app and always loading them would only increase overall response times and fill up the database without adding much value for the app.

For example the "dogma" consists of 4 models that relate to inventory types and contain specifics for type objects like the rate of fire for some ship modules. Not every app may need that additional information in their database.

Therefore the following eve models are not loaded through relations By default and need to be turned on explicitly:

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
.. Hint::
    You can still load objects from disabled models directly - e.g. with ``get_or_create_esi()`` - but be mindful that relations will not be created automatically, which can lead to inconsistencies in your database.
```

There are two solutions for loading disabled models incl. their relations:

- Globally enabling disabled models
- Enabling disabled models on-demand

```eval_rst
.. note::
    Related models that are disabled by default are also called sections.
```

#### Globally enabling models

One solution here is to offer developers control over which related models are loaded through configuration. Each disabled model therefore as a corresponding setting that can be used to globally enable that model.

```eval_rst
.. hint::
    When turning on loading of related models you usually want to reload related eve objects that already exist in the database to make sure all relations are created correctly. e.g. after turning on ``EveStargate`` you want to reload all solar systems.
```

```eval_rst
.. seealso::
    For an overview of all settings please see :ref:`operations-settings`.
```

### Load related models on-demand

However, globally enabling those related models will affect all apps of a Django installation. For instance if you turn on dogmas globally, dogmas will be loaded for each and every type, even if it that extra data is not needed.

This might not be the best option for some use cases and we are therefore offering an alternative solution. You can also activate disabled models on-demand.

#### Queries

Most manager methods like `get_or_create_esi()` and `update_or_create_esi()` take an extra argument called `enabled_sections`, which allows you to ensure specific sections are loaded with your query.

For example you may want to load planets just for one solar system. Here is how such a request might look like. Note that eveuniverse will automatically load missing planets from ESI for that solar system, even if it already exist in the local database.

```python
obj, _ = EveSolarSystem.objects.get_or_create_esi(id=30000142, include_children=True, enabled_sections=[EveSolarSystem.Section.PLANETS])
```

You can also specify multiple sections with one query. Here is how to fetch planets and their respective moons (a section of EvePlanet) on demand:

```python
obj, _ = EveSolarSystem.objects.get_or_create_esi(id=30000142, include_children=True, enabled_sections=[EveSolarSystem.Section.PLANETS, EvePlant.Section.MOONS])
```

See also the API for a list of all available sections for each model that supports it, e.g. `EvePlanet`, `EveSolarSystem`, `EveType`.

### Preloading instances

`eveuniverse_load_types` management command for preloading types can also include loading dogmas if requested.

### Test tools

The test tool for creating [test data](#test-data) also support the `enabled_sections` argument.

### Preloading data

While all models support loading eve objects on demand from ESI, some apps might need specific data sets to be preloaded. For example an app might want to provide a drop down list of all structure types, and loading that list on demand would not be fast enough to guarantee acceptable UI response times.

The solution is to provide the user with a management command, so he an preload the needed data sets - for example all ship types - during app installation. Since this is a command use case *django-eveuniverse* offers a management helper command with all the needed functionality for loading data and which can be easily utilized with just a very small and simple management command in your own app.

Here is an example for creating such a management command. We want to load all kinds of structures to show to the user in a drop down list. We therefore want to preload all structure types (`category_id = 65`), all control towers (`group_id = 365`) and the customs office (`type_id = 2233`):

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

```eval_rst
.. seealso::
    For an overview of all management commands please see :ref:`operations-management-commands`.
```

## Eve ID to name resolution

A common problem when working with data from ESI is the need to resolve the ID of an Eve object to it's name. To make this easier *django-eveuniverse* provides a dedicated model called `EveEntity`. `EveEntity` allows you to quickly resolve large amounts of Eve IDs to objects in bulk, with every object having it's name and entity category. Resolved objects are stored locally and automatically used to speed up subsequent ID resolving.

Here is a simple example for resolving the ID of the Jita solar system:

```python
>>> EveEntity.objects.resolve_name(30000142)
'Jita'
```

```eval_rst
.. note::
    Eve IDs have unique ranged for the supported categories, which means they can be safely resolved without having to specify a category.
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

```eval_rst
.. hint::
    If you need to test that an ID is valid you can use ``get_or_create_esi()`` or ``update_or_create_esi()``. Both will return  ``None`` instead of an ``EveEntity`` object if the given ID was not valid. You can also use ``resolve_name()``, which will return an empty string for invalid IDs.

    However, calling ESI with an invalid ID will also count against the error rate limit, so use with care.

```

```eval_rst
.. seealso::
    For more features and details please see :ref:`api-managers-eve-entity`.

```

```eval_rst
.. _developer-testdata:
```

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
        testdata_spec = [
            ModelSpec("EveFaction", ids=[500001]),
            ModelSpec(
                "EveType",
                ids=[603, 621, 638, 2488, 2977, 3756, 11379, 16238, 34562, 37483],
            ),
            ModelSpec(
                "EveSolarSystem", ids=[30001161, 30004976, 30004984, 30045349, 31000005],
            ),
            ModelSpec("EveRegion", ids=[10000038], include_children=True),
        ]
        create_testdata(testdata_spec, test_data_filename())

```

### Using generated testdata in your tests

To utilize the generated testdata file in your test you need another script that creates objects from your generated JSON file.

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
