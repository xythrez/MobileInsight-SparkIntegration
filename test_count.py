#!/usr/bin/env python3
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mobile_insight.analyzer.analyzer import Analyzer
from mobile_insight.monitor.monitor import Event
from mobile_insight_dev.monitor import SparkReplayer

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

    @classmethod
    def spark_export(cls, analyzer):
        return analyzer.attach_accept_count

    @classmethod
    def spark_collect(cls, list_of_results):
        return sum(list_of_results)


def main():
    src = SparkReplayer()
    src.set_input_path("./logs")

    analyzer = myAnalyzer()
    analyzer.set_source(src)  # bind with the monitor

    src.run()

    # New monkeypatching function. All analyzers registered with SparkReplayer
    # automatically get a new .collect() function that returns multiple
    # instances of itself containing the execution results.
    #
    # Register a spark_collect using SparkReplayer.set_analyzer_callbacks() to
    # manually combine the results of each instance together
    collection = analyzer.collect()
    print(collection)


if __name__ == '__main__':
    main()
