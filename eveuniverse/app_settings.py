from .utils import clean_setting

EVEUNIVERSE_BULK_METHODS_BATCH_SIZE = clean_setting(
    "EVEUNIVERSE_BULK_METHODS_BATCH_SIZE", 500
)
# Technical parameter defining the maximum number of objects processed per run
# of Django batch methods, e.g. bulk_create and bulk_update


EVEUNIVERSE_LOAD_ASTEROID_BELTS = clean_setting(
    "EVEUNIVERSE_LOAD_ASTEROID_BELTS", False
)
"""When true will automatically load astroid belts with every solar system."""

EVEUNIVERSE_LOAD_DOGMAS = clean_setting("EVEUNIVERSE_LOAD_DOGMAS", False)
"""When true will automatically load dogma, e.g. with every type."""

EVEUNIVERSE_LOAD_GRAPHICS = clean_setting("EVEUNIVERSE_LOAD_GRAPHICS", False)
"""When true will automatically load graphics with every type."""

EVEUNIVERSE_LOAD_MARKET_GROUPS = clean_setting("EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
"""When true will automatically load market groups with every type."""

EVEUNIVERSE_LOAD_MOONS = clean_setting("EVEUNIVERSE_LOAD_MOONS", False)
"""When true will automatically load moons be with every planet."""

EVEUNIVERSE_LOAD_PLANETS = clean_setting("EVEUNIVERSE_LOAD_PLANETS", False)
"""When true will automatically load planets with every solar system."""

EVEUNIVERSE_LOAD_STARGATES = clean_setting("EVEUNIVERSE_LOAD_STARGATES", False)
"""When true will automatically load stargates with every solar system."""

EVEUNIVERSE_LOAD_STARS = clean_setting("EVEUNIVERSE_LOAD_STARS", False)
"""When true will automatically load stars with every solar system."""

EVEUNIVERSE_LOAD_STATIONS = clean_setting("EVEUNIVERSE_LOAD_STATIONS", False)
"""When true will automatically load stations be with every solar system."""

EVEUNIVERSE_LOAD_TYPE_MATERIALS = clean_setting(
    "EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
)
"""When true will automatically load type materials be with every type."""

EVEUNIVERSE_TASKS_TIME_LIMIT = clean_setting("EVEUNIVERSE_TASKS_TIME_LIMIT", 7200)
"""Global timeout for tasks in seconds to reduce task accumulation during outages."""

EVEUNIVERSE_USE_EVESKINSERVER = clean_setting("EVEUNIVERSE_USE_EVESKINSERVER", True)
"""When True a call to EveType.icon_url for a SKIN type will return a eveskinserver URL
else it will return a generic SKIN icon.
"""
