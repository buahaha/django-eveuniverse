"""helper functions for using Eve Universe"""


def meters_to_ly(value: float) -> float:
    """converts meters into lightyears"""
    return float(value) / 9_460_730_472_580_800 if value is not None else None


def meters_to_au(value: float) -> float:
    """converts meters into AU"""
    return float(value) / 149_597_870_691 if value is not None else None
