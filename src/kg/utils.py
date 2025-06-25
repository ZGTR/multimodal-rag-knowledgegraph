def get_first(val):
    if isinstance(val, list):
        return val[0] if val else None
    return val 