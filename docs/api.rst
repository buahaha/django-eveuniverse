.. currentmodule:: eveuniverse

===============
API
===============

This chapter contains the developer reference documentation of the public API for *django-eveuniverse* consisting of all models, their manager methods and helpers.

.. _api-eve-models:

Base classes
============

.. autoclass:: eveuniverse.models.EveUniverseBaseModel
    :members:

.. autoclass:: eveuniverse.models.EveUniverseEntityModel
    :members:


Core functions
==============

esitools
----------------
.. automodule:: eveuniverse.core.esitools
    :members:

eveimageserver
----------------
.. automodule:: eveuniverse.core.eveimageserver
    :members:

Eve Models
==========

EveAncestry
----------------
.. autoclass:: eveuniverse.models.EveAncestry
    :members:

EveAsteroidBelt
----------------
.. autoclass:: eveuniverse.models.EveAsteroidBelt
    :members:

EveBloodline
----------------
.. autoclass:: eveuniverse.models.EveBloodline
    :members:

EveCategory
----------------
.. autoclass:: eveuniverse.models.EveCategory
    :members:


EveConstellation
----------------
.. autoclass:: eveuniverse.models.EveConstellation
    :members:

EveDogmaAttribute
-----------------
.. autoclass:: eveuniverse.models.EveDogmaAttribute
    :members:

EveDogmaEffect
--------------
.. autoclass:: eveuniverse.models.EveDogmaEffect
    :members:

.. _api-models-eve-entity:

EveDogmaEffectModifier
----------------------
.. autoclass:: eveuniverse.models.EveDogmaEffectModifier
    :members:

Eve Entity
--------------

.. autoclass:: eveuniverse.models.EveEntity
    :members:
    :exclude-members:  DoesNotExist,  MultipleObjectsReturned

EveFaction
----------
.. autoclass:: eveuniverse.models.EveFaction
    :members:

EveGraphic
----------
.. autoclass:: eveuniverse.models.EveGraphic
    :members:

EveGroup
----------
.. autoclass:: eveuniverse.models.EveGroup
    :members:

EveMarketGroup
--------------
.. autoclass:: eveuniverse.models.EveMarketGroup
    :members:

EveMarketPrice
--------------
.. autoclass:: eveuniverse.models.EveMarketPrice
    :members:

EveMoon
----------
.. autoclass:: eveuniverse.models.EveMoon
    :members:

EvePlanet
----------
.. autoclass:: eveuniverse.models.EvePlanet
    :members:

EveRace
----------
.. autoclass:: eveuniverse.models.EveRace
    :members:

EveRegion
----------
.. autoclass:: eveuniverse.models.EveRegion
    :members:

EveSolarSystem
--------------
.. autoclass:: eveuniverse.models.EveSolarSystem
    :members:
    :exclude-members: children

EveStar
----------
.. autoclass:: eveuniverse.models.EveStar
    :members:

EveStargate
-----------
.. autoclass:: eveuniverse.models.EveStargate
    :members:
    :exclude-members:  children, inline_objects

EveStation
----------
.. autoclass:: eveuniverse.models.EveStation
    :members:

EveStationService
-----------------
.. autoclass:: eveuniverse.models.EveStationService
    :members:

EveType
---------
.. autoclass:: eveuniverse.models.EveType
    :members:

EveTypeDogmaAttribute
---------------------
.. autoclass:: eveuniverse.models.EveTypeDogmaAttribute
    :members:

EveTypeDogmaEffect
------------------
.. autoclass:: eveuniverse.models.EveTypeDogmaEffect
    :members:

EveUnit
---------
.. autoclass:: eveuniverse.models.EveUnit
    :members:

.. _api-manager-methods:

Manager methods
====================

Default manager methods
-------------------------

All eve models have the following manager methods:

.. autoclass:: eveuniverse.managers.EveUniverseEntityModelManager
    :members:

.. _api-managers-eve-entity:

EveEntity manager methods
-------------------------

EveEntity comes with some additional manager methods.

.. autoclass:: eveuniverse.managers.EveEntityQuerySet
    :members:

.. autoclass:: eveuniverse.managers.EveEntityManager
    :members: get_or_create_esi, update_or_create_esi, bulk_create_esi, bulk_update_new_esi, bulk_update_all_esi, resolve_name, bulk_resolve_names

Other manager methods
-------------------------

.. autoclass:: eveuniverse.managers.EveMarketPriceManager
    :members:

Helpers
====================

.. autoclass:: eveuniverse.helpers.EveEntityNameResolver
    :members: to_name

.. autofunction:: eveuniverse.helpers.meters_to_au

.. autofunction:: eveuniverse.helpers.meters_to_ly

Tasks
====================

Eve Universe tasks
------------------

.. autofunction:: eveuniverse.tasks.load_eve_object

.. autofunction:: eveuniverse.tasks.update_or_create_eve_object

EveEntity tasks
---------------

.. autofunction:: eveuniverse.tasks.create_eve_entities

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities

Object loader tasks
-------------------

.. autofunction:: eveuniverse.tasks.create_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.load_map

.. autofunction:: eveuniverse.tasks.load_eve_types

Other tasks
-------------------

.. autofunction:: eveuniverse.tasks.update_market_prices

Tools
====================

Testdata
-------------------

.. automodule:: eveuniverse.tools.testdata
    :members:

.. seealso::
    Please also see :ref:`developer-testdata` on how to create test data for your app.
