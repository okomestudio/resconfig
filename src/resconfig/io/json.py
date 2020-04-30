from json import dump as _dump
from json import load as _load
from json.decoder import JSONDecodeError

from ..ondict import ONDict


def dump(content, f, spec=None):
    return _dump(content, f)


def load(f):
    try:
        content = _load(f)
    except JSONDecodeError:
        content = {}
    return ONDict(content)
