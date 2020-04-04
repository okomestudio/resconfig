import os
from collections.abc import MutableMapping
from tempfile import NamedTemporaryFile

import pytest


def generate_normedkeys(dic, parents=None):
    parents = parents or list()
    for key, val in dic.items():
        if isinstance(val, MutableMapping):
            for k in generate_normedkeys(val, parents + [key]):
                yield k
        else:
            yield ".".join(parents + [key])


_default_config = {
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
def default_config():
    yield _default_config


@pytest.fixture(params=generate_normedkeys(_default_config))
def default_config_key(request):
    yield request.param


@pytest.fixture
def all_default_config_keys(default_config):
    keys = list(generate_normedkeys(default_config))
    yield keys


@pytest.fixture
def filename():
    f = NamedTemporaryFile(delete=False)
    filename = f.name
    yield filename
    os.remove(filename)
