import yaml

from ..dicttype import Dict


class _Dumper(yaml.Dumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


_Dumper.add_representer(Dict, _dict_representer)


def dump(data, stream, **kwargs):
    yaml.dump(data, stream, _Dumper, **kwargs)


def load(stream, **kwargs):
    return yaml.load(stream, yaml.FullLoader, **kwargs)
