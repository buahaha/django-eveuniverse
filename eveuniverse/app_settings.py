from .utils import clean_setting

# Technical parameter defining the maximum number of objects processed per run
# of Django batch methods, e.g. bulk_create and bulk_update
EVEUNIVERSE_BULK_METHODS_BATCH_SIZE = clean_setting(
    "EVEUNIVERSE_BULK_METHODS_BATCH_SIZE", 500
)

# when true will automatically load astroid belts with every solar system
EVEUNIVERSE_LOAD_ASTEROID_BELTS = clean_setting(
    "EVEUNIVERSE_LOAD_ASTEROID_BELTS", False
)

# when true will automatically load dogma, e.g. with every type
EVEUNIVERSE_LOAD_DOGMAS = clean_setting("EVEUNIVERSE_LOAD_DOGMAS", False)

# when true will automatically load graphics with every type
EVEUNIVERSE_LOAD_GRAPHICS = clean_setting("EVEUNIVERSE_LOAD_GRAPHICS", False)

# when true will automatically load market groups with every type
EVEUNIVERSE_LOAD_MARKET_GROUPS = clean_setting("EVEUNIVERSE_LOAD_MARKET_GROUPS", False)

# when true will automatically load moons be with every planet
EVEUNIVERSE_LOAD_MOONS = clean_setting("EVEUNIVERSE_LOAD_MOONS", False)

# when true will automatically load planets with every solar system
EVEUNIVERSE_LOAD_PLANETS = clean_setting("EVEUNIVERSE_LOAD_PLANETS", False)

# when true will automatically load stargates with every solar system
EVEUNIVERSE_LOAD_STARGATES = clean_setting("EVEUNIVERSE_LOAD_STARGATES", False)

# when true will automatically load stars with every solar system
EVEUNIVERSE_LOAD_STARS = clean_setting("EVEUNIVERSE_LOAD_STARS", False)

# when true will automatically load stations be with every solar system
EVEUNIVERSE_LOAD_STATIONS = clean_setting("EVEUNIVERSE_LOAD_STATIONS", False)

# Global timeout for tasks in seconds to reduce task accumulation during outages
EVEUNIVERSE_TASKS_TIME_LIMIT = clean_setting("EVEUNIVERSE_TASKS_TIME_LIMIT", 7200)
