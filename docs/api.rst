.. currentmodule:: eveuniverse

===============
API
===============

Relationship diagramm
=====================

The following graph shows all models and how they are interrelated:

.. image:: https://i.imgur.com/FYYihzt.png
   :target: https://i.imgur.com/FYYihzt.png

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

EveType
---------
.. autoclass:: eveuniverse.models.EveType
    :members: 

EveUnit
---------
.. autoclass:: eveuniverse.models.EveUnit
    :members: 

Manager methods
====================

Eve Models
----------

All eve models have the following manager methods:

.. autoclass:: eveuniverse.managers.EveUniverseEntityModelManager
    :members:

EveEntity
----------

EveEntity comes with some additional manager methods.

.. autoclass:: eveuniverse.managers.EveEntityQuerySet
    :members:

.. autoclass:: eveuniverse.managers.EveEntityManager
    :members:
    :exclude-members: get_queryset, update_or_create_all_esi
