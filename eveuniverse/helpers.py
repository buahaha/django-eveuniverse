from typing import Dict


def meters_to_ly(value: float) -> float:
    """converts meters into lightyears"""
    return float(value) / 9_460_730_472_580_800 if value is not None else None


def meters_to_au(value: float) -> float:
    """converts meters into AU"""
    return float(value) / 149_597_870_691 if value is not None else None


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
