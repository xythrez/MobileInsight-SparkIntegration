from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mobile_insight.monitor import OfflineReplayer
from mobile_insight.analyzer.analyzer import *
import sys
import time
import timeit
import io
from mobile_insight.monitor.monitor import Event
from mobile_insight.monitor.offline_replayer import *
from mobile_insight.monitor.dm_collector import dm_collector_c, DMLogPacket


class myAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.add_source_callback(self.__msg_callback)
        self.attach_accept_count = 0

    def set_source(self, source):
        """
        Set the trace source. Enable the cellular signaling messages

        :param source: the trace source (collector).
        """
        Analyzer.set_source(self, source)
        source.enable_log("LTE_NAS_ESM_OTA_Incoming_Packet")
        #source.enable_log("LTE_NAS_ESM_OTA_Outgoing_Packet")
        source.enable_log("LTE_NAS_EMM_OTA_Incoming_Packet")
        #source.enable_log("LTE_NAS_EMM_OTA_Outgoing_Packet")
        # source.enable_log("LTE_RRC_OTA_Packet")
        # source.enable_log_all()    

    def __msg_callback(self, msg):
        if msg.type_id == "LTE_NAS_ESM_OTA_Incoming_Packet" or msg.type_id == "LTE_NAS_EMM_OTA_Incoming_Packet":
            data = msg.data.decode()
            if 'Msg' in data.keys():
                log_xml = ET.XML(data['Msg'])
                #print('x')
            else:
                return
            xml_msg = Event(msg.timestamp, msg.type_id, log_xml)
            for field in xml_msg.data.iter('field'):
                if field.get('name') != None and 'nas_eps.nas_msg' in field.get('name'):
                    if field.get('showname') == 'NAS EPS Mobility Management Message Type: Attach accept (0x42)':
                        self.attach_accept_count += 1



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
    Analyzer.reset()
    src = ByteArrayReplayer(content)
    analyzer = myAnalyzer()
    analyzer.set_source(src)
    src.run()
    return analyzer.attach_accept_count



def main():
    # Initialize SparkSession
    spark = SparkSession.builder \
        .appName("Log Processor") \
        .master("spark://localhost:7077") \
        .getOrCreate()

    # Define a UDF that wraps the external parsing function
    parse_udf = udf(parse_binary_data, IntegerType())

    # Read binary files from a specified directory
    binary_files_df = spark.read.format("binaryFile") \
        .option("pathGlobFilter", "*.qmdl") \
        .load("./logs/")

    # Apply the UDF to parse the binary data
    parsed_data = binary_files_df.withColumn("parsed_result", parse_udf(binary_files_df["content"]))

    # Aggregate the results to get a total count
    total_count = parsed_data.selectExpr("sum(parsed_result) as total").collect()[0]['total']

    # Print the total count
    print(f"Total count from all files: {total_count}")

    # Stop the Spark session
    spark.stop()

if __name__ == '__main__':
    main()
