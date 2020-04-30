from ..ondict import ONDict

try:
    import yaml
except ImportError:
    yaml = None


def dump(data, stream, spec=None, **kwargs):
    class _Dumper(yaml.Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
        )

    _Dumper.add_representer(ONDict, _dict_representer)

    yaml.dump(data, stream, _Dumper, **kwargs)


def load(stream, **kwargs):
    content = yaml.load(stream, yaml.FullLoader, **kwargs)
    return ONDict(content if content else {})
