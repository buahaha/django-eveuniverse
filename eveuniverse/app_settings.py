from .utils import clean_setting

# when true will automatically load dogma, e.g. with every type
EVEUNIVERSE_LOAD_DOGMAS = clean_setting("EVEUNIVERSE_LOAD_DOGMAS", False)

# when true will automatically load market groups, e.g. with every type
EVEUNIVERSE_LOAD_MARKET_GROUPS = clean_setting("EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
