from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight_dev.analyzer.spark_msglogger import SparkMsgLogger


if __name__ == "__main__":

    # Initialize a monitor
    src = SparkReplayer()
    src.set_input_path("./logs/")
    # src.enable_log_all()

    src.enable_log("LTE_PHY_Serv_Cell_Measurement")
    src.enable_log("5G_NR_RRC_OTA_Packet")
    src.enable_log("LTE_RRC_OTA_Packet")
    src.enable_log("LTE_NB1_ML1_GM_DCI_Info")

    logger = SparkMsgLogger()
    logger.set_decode_format(SparkMsgLogger.XML)
    logger.set_dump_type(SparkMsgLogger.FILE_ONLY)
    logger.save_decoded_msg_as("./test.txt")
    logger.set_source(src)
    src.run()
    logger.collect()