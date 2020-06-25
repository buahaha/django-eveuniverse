"""helper functions for using the Eve SDE"""


def meters_to_ly(value: float) -> float:
    """converts meters into lightyears"""
    return float(value) / 9_460_730_472_580_800 if value is not None else None
    # $distance = sqrt(pow($x2-$x1,2)+pow($y2-$y1,2)+pow($z2-$z1,2))/9.4605284e15


def meters_to_au(value: float) -> float:
    """converts meters into AU"""
    return float(value) / 149_597_870_691 if value is not None else None
