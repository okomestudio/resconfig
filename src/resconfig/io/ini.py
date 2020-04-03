from configparser import ConfigParser

from ..dicttype import Dict


def load(f):
    parser = ConfigParser()
    parser.read_file(f)
    dic = Dict()
    for section in parser.sections():
        ref = dic.setdefault(section, Dict())
        for option in parser[section]:
            ref[option] = parser[section][option]
    return dic


def dump(content, f):
    if _depth(content) > 2:
        raise ValueError("INI config does not allow nested options")

    parser = ConfigParser()
    parser.read_dict(content)
    parser.write(f)


def _depth(obj, depth=0):
    if not isinstance(obj, dict):
        return depth
    max_depth = depth
    for key in obj:
        max_depth = max(max_depth, _depth(obj[key], depth + 1))
    return max_depth
