from typing import Dict, Optional

from django.db import models


def meters_to_ly(value: float) -> float:
    """converts meters into lightyears"""
    return float(value) / 9_460_730_472_580_800 if value is not None else None


def meters_to_au(value: float) -> float:
    """converts meters into AU"""
    return float(value) / 149_597_870_691 if value is not None else None


def get_or_create_esi_or_none(
    prop_name: str, dct: dict, Model: type
) -> Optional[models.Model]:
    """tries to create a new eveuniverse object from a dictionary entry

    return the object on success or None
    """
    if dct.get(prop_name):
        obj, _ = Model.objects.get_or_create_esi(id=dct.get(prop_name))
    else:
        obj = None

    return obj


class EveEntityNameResolver:
    """Container with a mapping between entity Ids and entity names
    and a performant API
    """

    def __init__(self, names_map: Dict[int, str]) -> None:
        self._names_map = names_map

    def to_name(self, id: int) -> str:
        """Resolved an entity ID to a name

        Args:
            id: ID of the Eve entity to resolve

        Returns:
            name for corresponding entity ID if known else an empty string
        """
        try:
            name = self._names_map[id]
        except KeyError:
            name = ""

        return name
