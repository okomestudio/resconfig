import yaml
from collections import OrderedDict


class _OrderedDumper(yaml.Dumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


_OrderedDumper.add_representer(OrderedDict, _dict_representer)


def dump(data, stream, **kwargs):
    yaml.dump(data, stream, _OrderedDumper, **kwargs)


def load(stream, **kwargs):
    return yaml.load(stream, yaml.FullLoader, **kwargs)
