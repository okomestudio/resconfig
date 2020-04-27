from datetime import datetime

from .ondict import ONDict


class ddef:
    vtype = None
    nullable = False

    def __init__(self, value, doc=None):
        super().__init__()
        if not isinstance(value, self.vtype):
            raise ValueError("%s is not of %s type", value, self.vtype)
        self.value = value
        self.doc = doc

    @classmethod
    def cast(cls, value):
        return cls.vtype(value)


class nullable:
    nullable = True

    @classmethod
    def cast(cls, value):
        if value is None:
            return None
        return super().cast(value)


class bool_(ddef):
    vtype = bool


class bool_or_none(nullable, bool_):
    pass


class datetime_(ddef):
    vtype = datetime


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
