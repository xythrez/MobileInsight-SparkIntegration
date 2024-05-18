import os
from threading import Lock
from pyspark.sql import SparkSession
from pyspark.sql.functions import posexplode
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    LongType,
    BinaryType,
    ArrayType,
)

from mobile_insight.monitor import OfflineReplayer
from .decoder import SparkDecoder


class SparkReplayer(OfflineReplayer):
    '''Spark-backend OfflineReplayer

    This Replayer is only available if PySpark is installed
    '''

    _reflock = Lock()
    _refcnt = 0
    _spark = None

    def __init__(self):
        OfflineReplayer.__init__(self)

        # Keep a reference count of SparkReplayers
        #
        # Spark already provides a way to create sessions once using
        # getOrCreate(), but this allows us to terminate the session
        # once all references are lost.
        with SparkReplayer._reflock:
            if SparkReplayer._refcnt == 0:
                # Use the Spark URL in the MI_SPARK_URL variable,
                # fallback to pyspark's local session if unavailable
                mi_spark_url = os.getenv('MI_SPARK_URL', 'local[1]')
                # Only print Spark logs error or above by default
                mi_log_level = os.getenv('MI_SPARK_LOG_LEVEL', 'error')
                SparkReplayer._spark = (SparkSession.builder
                                        .master(mi_spark_url)
                                        .appName('mobile_insight')
                                        .getOrCreate())
                SparkReplayer._spark.sparkContext.setLogLevel(mi_log_level)
            SparkReplayer._refcnt += 1

        self._sampling_rate = -1
        self._output_path = None

    def __del__(self):
        # Decrease reference on garbage collection
        # If refcnt drops to 0, stop the SparkSession
        with SparkReplayer._reflock:
            SparkReplayer._refcnt -= 1
            if SparkReplayer._refcnt == 0:
                try:
                    SparkReplayer._spark.stop()
                # For some reason stop() is async, which means it could be
                # called twice during python shutdown.
                # Simply ignore the error and move on if this happens.
                except ImportError:
                    pass

        OfflineReplayer.__del__(self)

    def set_sampling_rate(self, sampling_rate):
        OfflineReplayer.set_sampling_rate(self, sampling_rate)
        # Need to propagate this to SubMonitors
        self._sampling_rate = sampling_rate

    def save_log_as(self, path):
        # Do not call the OfflineReplayer version. It opens the file
        # immediately.
        # Instead, save the path and create a directory with the files
        # during execution.
        os.makedirs(path, exist_ok=True)
        self._output_path = path

    def set_partition_function(self, func):
        pass

    def set_gather_function(self, func):
        pass

    def run(self):
        # Collect data from both qmdl and mi2logs
        logs = (SparkReplayer
                ._spark.read.format("binaryFile")
                .option("pathGlobFilter", "*.qmdl")
                .load(self._input_path))
        logs = logs.union(SparkReplayer
                          ._spark.read.format("binaryFile")
                          .option("pathGlobFilter", "*.mi2log")
                          .load(self._input_path))

        schema = StructType([
            StructField('file_path', StringType(), False),
            StructField('file_mtime', TimestampType(), False),
            StructField('file_packets', LongType(), False),
            StructField('content', ArrayType(StructType([
                StructField('timestamp', TimestampType(), False),
                StructField('type_id', StringType(), False),
                StructField('packet', BinaryType(), False),
            ])), False),
        ])

        decoded = logs.rdd.map(lambda x:
                               SparkDecoder(os.path.basename(x.path),
                                            self._output_path,
                                            self._sampling_rate,
                                            self._type_names,
                                            self._skip_decoding)
                               .decode(x)).toDF(schema)
        decoded = (decoded.select(decoded['*'], posexplode(decoded.content))
                   .drop('content')
                   .withColumnRenamed('pos', 'order')
                   .select('*', 'col.timestamp', 'col.type_id', 'col.packet')
                   .drop('col'))



        # TODO: Distribute tasks
        # TODO: Spawn a stateful submonitor for each task
        # TODO: Collect results

        decoded.show(n=10, truncate=False)
