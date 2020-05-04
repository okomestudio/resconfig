from datetime import datetime

import pytest

from resconfig.fields import Bool
from resconfig.fields import Datetime
from resconfig.fields import Float
from resconfig.fields import Int
from resconfig.fields import NullableBool
from resconfig.fields import NullableDatetime
from resconfig.fields import NullableFloat
from resconfig.fields import NullableInt
from resconfig.fields import NullableStr
from resconfig.fields import Str


class Base:
    @pytest.fixture
    def field(self):
        return self.field_type()

    def test_from_obj(self, field):
        assert isinstance(field.from_obj(field.value), field.ftype)

    def test_to_str(self, field):
        assert field.to_str(field.value) == self.to_str_expected

    def test_to_str_wrong_type(self, field):
        with pytest.raises(TypeError):
            field.to_str(None)


class TestBool(Base):
    field_type = Bool
    to_str_expected = "false"


class TestDatetime(Base):
    field_type = Datetime
    to_str_expected = "1969-12-31T16:00:00"

    @pytest.mark.parametrize(
        "obj, expected",
        [
            (datetime.fromtimestamp(0), datetime.fromtimestamp(0)),
            ("1969-12-31T16:00:00", datetime.fromtimestamp(0)),
            (0, datetime.fromtimestamp(0)),
        ],
    )
    def test_from_obj(self, field, obj, expected):
        result = field.from_obj(obj)
        assert isinstance(result, field.ftype)
        assert result == expected

    def test_from_obj_invalid_input(self, field):
        with pytest.raises(ValueError):
            field.from_obj(object())


class TestFloat(Base):
    field_type = Float
    to_str_expected = "0.0"


class TestInt(Base):
    field_type = Int
    to_str_expected = "0"


class TestStr(Base):
    field_type = Str
    to_str_expected = ""


class BaseNullable:
    @pytest.fixture
    def field(self):
        return self.field_type()

    def test_nullable_default(self, field):
        assert field.default is None
        assert field.value is None

    def test_nullable_from_obj(self, field):
        assert isinstance(field.from_obj(self.to_str_expected), field.ftype)

    def test_nullable_from_obj_with_none(self, field):
        assert field.from_obj(None) is None

    def test_nullable_to_str(self, field):
        assert field.to_str(self.from_obj_expected) == self.to_str_expected

    def test_nullable_to_str_with_none(self, field):
        assert field.to_str(None) == "null"


class TestNullableBool(BaseNullable):
    field_type = NullableBool
    from_obj_expected = False
    to_str_expected = "false"


class TestNullableDatetime(BaseNullable):
    field_type = NullableDatetime
    from_obj_expected = datetime.fromtimestamp(0)
    to_str_expected = "1969-12-31T16:00:00"

    @pytest.mark.parametrize(
        "obj, expected",
        [
            (datetime.fromtimestamp(0), datetime.fromtimestamp(0)),
            ("1969-12-31T16:00:00", datetime.fromtimestamp(0)),
            (0, datetime.fromtimestamp(0)),
        ],
    )
    def test_from_obj(self, field, obj, expected):
        result = field.from_obj(obj)
        assert isinstance(result, field.ftype)
        assert result == expected

    def test_from_obj_invalid_input(self, field):
        with pytest.raises(ValueError):
            field.from_obj(object())


class TestNullableFloat(BaseNullable):
    field_type = NullableFloat
    from_obj_expected = 0.0
    to_str_expected = "0.0"


class TestNullableInt(BaseNullable):
    field_type = NullableInt
    from_obj_expected = 0
    to_str_expected = "0"


class TestNullableStr(BaseNullable):
    field_type = NullableStr
    from_obj_expected = ""
    to_str_expected = ""
