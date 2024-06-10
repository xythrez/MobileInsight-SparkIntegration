#!/usr/bin/python
"""
spark_msglogger.py

Author: Ziyue Dang
"""

from mobile_insight.analyzer.analyzer import Analyzer
import datetime
import json

class SparkMsgLogger(Analyzer):
    """
    A simple dumper to print messages
    """
    # Decoding scheme
    NO_DECODING = 0
    XML = 1
    JSON = 2
    DICT = 3

    # Dump type
    STDIO_ONLY = 4
    FILE_ONLY = 5
    ALL = 6

    def __init__(self, decode_type=0, dump_type=6):
        Analyzer.__init__(self)
        # a message dump has no analyzer in from/to_list
        # it only has a single callback for the source
        self.add_source_callback(self.__dump_message)
        self.__msg_log = []  # in-memory message log
        self.decode_type = decode_type
        self._save_file_path = None
        self._dump_type = dump_type

    @classmethod
    def spark_init(cls):
        return [cls.decode_type, cls._dump_type]

    def set_dump_type(self, dump_type):
        """
        Specify if dump message to stdio and/or file

        :param dump_type: the dump type
        :type dump_type: STDIO_ONLY, FILE_ONLY, ALL
        """
        if dump_type != self.STDIO_ONLY \
                and dump_type != self.FILE_ONLY \
                and dump_type != self.ALL:
            return
        self._dump_type = dump_type
        self.__class__.spark_init = lambda: [self.decode_type, dump_type]

    def set_decode_format(self, msg_format):
        """
        Configure the format of decoded message. If not set, the message will not be decoded

        :param msg_format: the format of the decoded message
        :type msg_format: NO_DECODING, XML, JSON or DICT
        """
        if msg_format != self.NO_DECODING \
                and msg_format != self.XML \
                and msg_format != self.JSON \
                and msg_format != self.DICT:
            return

        self.decode_type = msg_format
        self.__class__.spark_init = lambda: [msg_format, self._dump_type]

    def save_decoded_msg_as(self, filepath):
        """
        Save decoded messages as a plain-text file.
        If not called, by default MsgLogger will not save decoded results as file.

        :param filepath: the path of the file to be saved
        :type filepath: string
        """

        if not isinstance(filepath, str):
            return

        self._save_file_path = filepath

    def __dump_message(self, msg):
        """
        Print the received message

        :param msg: the received message
        """
        if not msg.data:
            return
        # self.__msg_log.append(msg)
        date = datetime.datetime.fromtimestamp(
            msg.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')
        # self.log_info(date+':'+msg.type_id)
        decoded_msg = ""
        if self.decode_type == self.XML:
            decoded_msg = msg.data.decode_xml()
        elif self.decode_type == self.JSON:
            decoded_msg = msg.data.decode_json()
            try:
                json_obj = json.loads(decoded_msg)
            except BaseException:
                return

            if msg.type_id != 'LTE_RRC_OTA_Packet':
                self.log_info(json_obj['timestamp'] + '  ' + msg.type_id)

            try:
                parse = json_obj['Msg']['msg']['packet']['proto'][3]
                self.log_info(
                    json_obj['timestamp'] +
                    '  ' +
                    msg.type_id +
                    ':' +
                    parse['field']['@showname'] +
                    '/' +
                    parse['field']['field'][1]['field'][1]['field']['@name'])
            except BaseException:
                pass
        elif self.decode_type == self.DICT:
            decoded_msg = msg.data.decode()
        else:
            return

        if self._dump_type == self.STDIO_ONLY or self._dump_type == self.ALL:
            self.log_info(decoded_msg)
        if self._dump_type == self.FILE_ONLY or self._dump_type == self.ALL:
            self.__msg_log.append(str(decoded_msg) + '\n')
    
    def collect(self):
        if self._save_file_path:
            with open(self._save_file_path, 'a') as f:
                for result in self.source.spark_results[self]:
                    for msg in result.__msg_log:
                        f.write(msg)
        return self.source.spark_results[self]