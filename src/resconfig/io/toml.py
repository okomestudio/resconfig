from ..ondict import ONDict
from ..typing import IO
from ..typing import Optional

try:
    from toml import dumps as _dump
    from toml import loads as _load
except ImportError:
    _dump = _load = None


def dump(content: ONDict, f: IO, schema: Optional[ONDict] = None):
    f.write(_dump(content.asdict()))


def load(f: IO, schema: Optional[ONDict] = None) -> ONDict:
    return ONDict(_load(f.read()))
