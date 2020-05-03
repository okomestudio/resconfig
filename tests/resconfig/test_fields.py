from datetime import datetime

import pytest

from resconfig.fields import Bool
from resconfig.fields import Datetime
from resconfig.fields import Float
from resconfig.fields import Int
from resconfig.fields import Nullable
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

    @pytest.fixture
    def nullable_field(self):
        return Nullable(self.field_type)(self.field_type.default)

    def test_nullable_default(self, nullable_field):
        f = Nullable(self.field_type)()
        assert f.default is None
        assert f.value is None

    def test_nullable_from_obj(self, nullable_field):
        assert isinstance(
            nullable_field.from_obj(nullable_field.value), nullable_field.ftype
        )

    def test_nullable_from_obj_with_none(self, nullable_field):
        assert nullable_field.from_obj(None) is None

    def test_nullable_to_str(self, nullable_field):
        assert nullable_field.to_str(nullable_field.value) == self.to_str_expected

    def test_nullable_to_str_with_none(self, nullable_field):
        assert nullable_field.to_str(None) == "null"

    def test_nullable_field_class_name(self, nullable_field):
        assert (
            nullable_field.__class__.__name__ == "Nullable" + self.field_type.__name__
        )


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
