#!/usr/bin/env python3

import sys
from pyspark.sql import SparkSession


def main():
    with SparkSession.builder \
                     .master('spark://localhost:7077') \
                     .appName('mobile_insight') \
                     .getOrCreate() as spark:
        text_file = spark.read.text(sys.argv[0])
        char_count = text_file.rdd.map(lambda x: len(x[0])) \
                              .reduce(lambda x, y: x + y)
    assert char_count == 580, f'incorrect char count: {char_count}'
    print('SUCCESS: PySpark is running correctly!')


if __name__ == '__main__':
    main()
