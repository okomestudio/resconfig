try:
    from toml import dumps as _dump
    from toml import loads as _load
except ImportError:
    _dump = _load = None


def load(f):
    return _load(f.read())


def dump(content, f):
    f.write(_dump(dict(content)))
