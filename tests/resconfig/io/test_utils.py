import os
from pathlib import Path

import pytest
from resconfig.io.utils import ensure_path


class TestEnsurePath:
    @pytest.mark.parametrize("path", ["/path/to", Path("/path/to")])
    def test_type(self, path):
        assert isinstance(ensure_path(path), Path)

    @pytest.mark.parametrize("path", ["~/tmp", Path("~/tmp")])
    def test_userexpansion(self, path):
        result = ensure_path(path)
        assert str(result).startswith(os.environ["HOME"])
