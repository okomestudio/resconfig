from datetime import datetime

from dateutil.parser import parse as dtparse

from .ondict import ONDict


class ddef:
    vtype = None
    nullable = False

    def __init__(self, value, doc=None, **kwargs):
        super().__init__(**kwargs)
        self.value = self.from_obj(value)
        self.doc = doc

    @classmethod
    def from_obj(cls, value):
        return cls.vtype(value)

    @classmethod
    def to_str(cls, value):
        return str(value)


class nullable:
    nullable = True

    @classmethod
    def from_obj(cls, value):
        if value is None:
            return None
        return super().from_obj(value)

    @classmethod
    def to_str(cls, value):
        if value is None:
            return "null"
        return super().to_str(value)


class bool_(ddef):
    vtype = bool

    @classmethod
    def to_str(cls, value):
        return "true" if value else "false"


class bool_or_none(nullable, bool_):
    pass


class datetime_(ddef):
    vtype = datetime

    @classmethod
    def from_obj(cls, value):
        if isinstance(value, datetime):
            pass
        elif isinstance(value, str):
            value = dtparse(value)
        elif isinstance(value, (float, int)):
            value = datetime.fromtimestamp(value)
        else:
            raise ValueError(f"invalid value for datetime: {value!r}")
        return value

    @classmethod
    def to_str(cls, value):
        return value.isoformat()


class datetime_or_none(nullable, datetime_):
    pass


class float_(ddef):
    vtype = float


class float_or_none(nullable, float_):
    pass


class int_(ddef):
    vtype = int


class int_or_none(nullable, int_):
    pass


class str_(ddef):
    vtype = str


class str_or_none(nullable, str_):
    pass


def extract_values(d: ONDict) -> ONDict:
    """Make a ONDict with only default values and no other type info."""
    valueonly = ONDict()
    valueonly._create = True
    for key in d.allkeys():
        v = d[key]
        if isinstance(v, ddef):
            v = v.value
        valueonly[key] = v
    return valueonly
