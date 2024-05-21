from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import *

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mobile_insight.monitor import OfflineReplayer
from mobile_insight.analyzer import LteDlRetxAnalyzer
import sys
import time
import timeit
import io
from mobile_insight.monitor.monitor import Event
from mobile_insight.monitor.offline_replayer import *
from mobile_insight.monitor.dm_collector import dm_collector_c, DMLogPacket


class ByteArrayReplayer(OfflineReplayer):
    def __init__(self, byte_array):
        super().__init__()
        self.byte_array = byte_array  # Store the raw byte array
    
    def run(self):
        try:
            self.broadcast_info('STARTED', {})
            self.log_info('STARTED: ' + str(time.time()))

            dm_collector_c.reset()
            self._input_stream = io.BytesIO(self.byte_array)  # Use BytesIO to mimic file behavior with byte arrays
            decoding_inter = 0
            sending_inter = 0

            while True:
                s = self._input_stream.read(64)
                if not s:
                    break

                dm_collector_c.feed_binary(s)
                decoded = dm_collector_c.receive_log_packet(self._skip_decoding,
                                                            True)  # include_timestamp

                if decoded:
                    before_decode_time = time.time()
                    packet = DMLogPacket(decoded[0])
                    type_id = packet.get_type_id()
                    after_decode_time = time.time()
                    decoding_inter += after_decode_time - before_decode_time

                    if type_id in self._type_names or type_id == "Custom_Packet":
                        event = Event(timeit.default_timer(),
                                    type_id,
                                    packet)
                        self.send(event)
                    after_sending_time = time.time()
                    sending_inter += after_sending_time - after_decode_time

            self.log_info('Decoding_inter: ' + str(decoding_inter))
            self.log_info('sending_inter: ' + str(sending_inter))

        except Exception as e:
            import traceback
            sys.exit(str(traceback.format_exc()))

        event = Event(timeit.default_timer(), 'Monitor.STOP', None)
        self.send(event)
        self.log_info("ByteArray processing is completed.")



def parse_binary_data(content):
    src = ByteArrayReplayer(content)
    analyzer = LteDlRetxAnalyzer()
    analyzer.set_source(src)
    src.run()
    mac_delay = 0.0
    mac_delay_sample = 0
    rlc_delay = 0.0
    rlc_delay_sample = 0

    for _, bearer in analyzer.bearer_entity.items():
        for item in bearer.mac_retx:
            mac_delay += item['mac_retx']
        mac_delay_sample += len(bearer.mac_retx)

        for item in bearer.rlc_retx:
            rlc_delay += item['rlc_retx']
        rlc_delay_sample += len(bearer.rlc_retx)

    avg_mac_delay = mac_delay / mac_delay_sample if mac_delay_sample > 0 else 0.0
    avg_rlc_delay = rlc_delay / rlc_delay_sample if rlc_delay_sample > 0 else 0.0

    return (avg_mac_delay, avg_rlc_delay)



def main():
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("Log Processor") \
        .master("spark://localhost:7077") \
        .getOrCreate()

    # Define the schema for the output of your UDF
    udf_schema = StructType([
        StructField("avg_mac_delay", FloatType(), nullable=False),
        StructField("avg_rlc_delay", FloatType(), nullable=False)
    ])

    # Create the UDF
    parse_udf = udf(parse_binary_data, udf_schema)
    # Read binary files from a specified directory
    binary_files_df = spark.read.format("binaryFile") \
        .option("pathGlobFilter", "*.qmdl") \
        .load("./logs/")

    # Apply the UDF to parse the binary data
    parsed_data = binary_files_df.withColumn("result", parse_udf(binary_files_df["content"]))

    # Select the results and file path
    results = parsed_data.select("path", "result.avg_mac_delay", "result.avg_rlc_delay")

    # Show the results
    results.show(truncate=False)

    # Stop the Spark session
    spark.stop()

if __name__ == '__main__':
    main()