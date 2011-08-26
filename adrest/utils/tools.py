def as_tuple(obj):
    """ Given obj return a tuple.
    """
    if isinstance(obj, tuple):
        return obj
    elif obj is None:
        return tuple()
    elif isinstance(obj, list):
        return tuple(obj)
    return (obj,)
