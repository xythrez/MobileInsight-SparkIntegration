__all__ = []

from importlib.util import find_spec


def has_module(name):
    try:
        return find_spec(name) is not None
    except ModuleNotFoundError:
        return False


if has_module('pyspark'):
    __all__ += [
        'SparkReplayer'
    ]
    from .spark.spark_replayer import SparkReplayer
