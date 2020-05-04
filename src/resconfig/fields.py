from datetime import datetime
from datetime import timezone
from functools import wraps

from dateutil.parser import parse as dtparse

from .ondict import ONDict


def checktype(f):
    @wraps(f)
    def deco(cls, value):
        if not isinstance(value, cls.ftype):
            raise TypeError(f"{value} is not {cls.ftype}")
        return f(cls, value)

    return deco


class Nullable:
    default = None

    @classmethod
    def from_obj(cls, value):
        if value is None or value == "null":
            return None
        return super().from_obj(value)

    @classmethod
    def to_str(cls, value):
        if value is None:
            return "null"
        return super().to_str(value)


class Field:
    ftype = None
    default = None

    def __init__(self, value=None, doc=None, **kwargs):
        super().__init__(**kwargs)
        self.value = self.default if value is None else self.from_obj(value)
        self.doc = doc

    @classmethod
    def from_obj(cls, value):
        return cls.ftype(value)

    @classmethod
    @checktype
    def to_str(cls, value):
        return str(value)


class Bool(Field):
    ftype = bool
    default = False

    @classmethod
    @checktype
    def to_str(cls, value):
        return "true" if value else "false"


class Datetime(Field):
    ftype = datetime
    default = datetime.fromtimestamp(0, timezone.utc)

    @classmethod
    def from_obj(cls, value):
        if isinstance(value, datetime):
            pass
        elif isinstance(value, str):
            value = dtparse(value)
        elif isinstance(value, (float, int)):
            value = datetime.fromtimestamp(value, timezone.utc)
        else:
            raise ValueError(f"invalid value for datetime: {value!r}")
        return value

    @classmethod
    @checktype
    def to_str(cls, value):
        return value.isoformat()


class Float(Field):
    ftype = float
    default = 0.0


class Int(Field):
    ftype = int
    default = 0


class Str(Field):
    ftype = str
    default = ""


# fmt: off
class NullableBool(Nullable, Bool): pass
class NullableDatetime(Nullable, Datetime): pass
class NullableFloat(Nullable, Float): pass
class NullableInt(Nullable, Int): pass
class NullableStr(Nullable, Str): pass
# fmt: on


def extract_values(d: ONDict) -> ONDict:
    """Make a ONDict with only default values and no other type info."""
    valueonly = ONDict()
    valueonly._create = True
    for key in d.allkeys():
        v = d[key]
        if isinstance(v, Field):
            v = v.value
        valueonly[key] = v
    return valueonly
