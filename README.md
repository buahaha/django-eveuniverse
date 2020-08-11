# Eve Universe

Complete set of Eve Online Universe models in Django with on-demand loading from ESI

![release](https://img.shields.io/pypi/v/django-eveuniverse?label=release) ![python](https://img.shields.io/pypi/pyversions/django-eveuniverse) ![django](https://img.shields.io/pypi/djversions/django-eveuniverse?label=django) ![pipeline](https://gitlab.com/ErikKalkoken/django-eveuniverse/badges/master/pipeline.svg) ![coverage](https://gitlab.com/ErikKalkoken/django-eveuniverse/badges/master/coverage.svg) ![Documentation Status](https://readthedocs.org/projects/django-eveuniverse/badge/?version=latest)![license](https://img.shields.io/badge/license-MIT-green) ![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

## Overview

*django-eveuniverse* is a foundation app meant to help speed up the development of Eve Online apps with Django and ESI. It provides all classic "static" Eve classes as Django models, including all relationships, ready to be used in your project. Furthermore, all Eve models have an on-demand loading mechanism for fetching new objects from ESI.

Here is an overview of the main features:

- Complete set of Eve Universe objects as Django models like regions, types or planets.
- On-demand loading mechanism that allows retrieving Eve universe objects ad-hoc from ESI
- Management commands for preloading often used sets of data like the map or ships types
- Eve models come with additional useful features, e.g. a route finder between solar systems or image URLs for types
- Special model EveEntity for quickly resolving Eve Online IDs to names
- Optional asynchronous loading of eve models and loading of all related children. (e.g. load all types for a specific group)

## Documentation

For details on how to install and use *django-eveuniverse* please see the [documentation](https://django-eveuniverse.readthedocs.io/en/latest/).
