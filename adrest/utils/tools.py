def as_tuple(obj):
    " Given obj return a tuple "

    if not obj:
        return tuple()

    if isinstance(obj, (tuple, set, list)):
        return tuple(obj)

    return obj,
