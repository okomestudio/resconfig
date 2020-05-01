from ..ondict import ONDict

try:
    from toml import dumps as _dump
    from toml import loads as _load
except ImportError:
    _dump = _load = None


def load(f, schema=None):
    return ONDict(_load(f.read()))


def dump(content, f, schema=None):
    f.write(_dump(dict(content)))
