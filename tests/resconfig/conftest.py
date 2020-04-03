import os
from tempfile import NamedTemporaryFile

import pytest


@pytest.fixture
def default_config():
    yield {
        "x1": 1,
        "x2": "text_x2",
        "x3": {
            "y1": 2,
            "y2": "text_x3.y2",
            "y3": {"z1": 3, "z2": "text_x3.y3.z2"},
            "y4": {"z1": 4, "z2": "text_x3.y4.z2"},
        },
        "x4": {
            "y1": 5,
            "y2": "text_x4.y2",
            "y3": {"z1": 6, "z2": "text_x4.y3.z2"},
            "y4": {"z1": 7, "z2": "text_x4.y4.z2"},
        },
    }


@pytest.fixture
def filename():
    f = NamedTemporaryFile(delete=False)
    filename = f.name
    yield filename
    os.remove(filename)
