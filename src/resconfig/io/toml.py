try:
    from toml import dumps as _dump
    from toml import loads as _load
except ImportError:
    raise ImportError("toml package is missing")


def load(f):
    return _load(f.read())


def dump(content, f):
    f.write(_dump(dict(content)))
