
from __future__ import with_statement

import yaml
try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

default_config = 'config.yaml'
config = None

def load(filename=default_config, **kwargs):
    return yaml.load(open(filename, "r"), Loader=Loader, **kwargs)

def dump(document, **kwargs):
    return yaml.dump(document, Dumper=Dumper, **kwargs)


def load_config(filename=default_config):
    global config
    config = load(filename)

def dump_config(filename=default_config):
    with open(filename, "w") as f:
        f.write(dump(config))
