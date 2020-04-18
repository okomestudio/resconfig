from functools import wraps


def experimental(f):
    """Note the decorated function or method is experimental."""

    @wraps(f)
    def func(*args, **kwargs):
        return f(*args, **kwargs)

    func.__doc__ = "*Experimental:* " + func.__doc__
    return func
