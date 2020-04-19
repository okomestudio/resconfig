try:
    import yaml
except ImportError:
    yaml = None

from ..ondict import ONDict


def dump(data, stream, **kwargs):
    class _Dumper(yaml.Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
        )

    _Dumper.add_representer(ONDict, _dict_representer)

    yaml.dump(data, stream, _Dumper, **kwargs)


def load(stream, **kwargs):
    return yaml.load(stream, yaml.FullLoader, **kwargs)
