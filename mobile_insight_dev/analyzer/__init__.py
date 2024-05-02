__all__ = []

from importlib.util import find_spec
if find_spec('pyspark') is not None:
    __all__ += [
        'SparkAnalyzer'
    ]
    from .spark.analyzer import SparkAnalyzer

