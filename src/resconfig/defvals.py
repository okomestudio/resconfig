from datetime import datetime

# This implementation may look a bit tricky.


class defval:
    vtype = None
    nullable = False

    def __init__(self, value, doc=None):
        if not isinstance(value, self.vtype):
            raise ValueError("%s is not of %s type", value, self.vtype)
        self.value = value
        self.doc = doc

    @classmethod
    def to_str(cls, value):
        return str(value)


class nullable:
    nullable = True

    @classmethod
    def to_str(cls, value):
        if value is None:
            return "null"
        return super().to_str(value)


class bool_(defval):
    vtype = bool


class bool_or_none(nullable, bool_):
    pass


class datetime_(defval):
    vtype = datetime

    @classmethod
    def to_str(cls, value):
        return value.isoformat()


class datetime_or_none(nullable, datetime_):
    pass


class float_(defval):
    vtype = float


class float_or_none(nullable, float_):
    pass


class int_(defval):
    vtype = int


class int_or_none(nullable, int_):
    pass


class str_(defval):
    vtype = str


class str_or_none(nullable, str_):
    pass
