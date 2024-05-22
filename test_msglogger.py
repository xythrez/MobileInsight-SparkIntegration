from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer import MsgLogger, NrRrcAnalyzer, LteRrcAnalyzer, WcdmaRrcAnalyzer, LteNasAnalyzer, UmtsNasAnalyzer, LteMacAnalyzer, LteMeasurementAnalyzer

def export_func(x):
    return None

if __name__ == "__main__":

    # Initialize a monitor
    src = SparkReplayer()
    src.set_input_path("./logs/")
    # src.enable_log_all()

    src.enable_log("LTE_PHY_Serv_Cell_Measurement")
    src.enable_log("LTE_RRC_OTA_Packet")
    src.enable_log("LTE_NB1_ML1_GM_DCI_Info")

    logger = MsgLogger()
    logger.set_decode_format(MsgLogger.XML)
    logger.set_dump_type(MsgLogger.FILE_ONLY)
    logger.save_decoded_msg_as("./test.txt")
    logger.set_source(src)
    src.set_analyzer_callbacks(logger, export_func=export_func)

    # # Analyzers
    nr_rrc_analyzer = NrRrcAnalyzer()
    nr_rrc_analyzer.set_source(src)  # bind with the monitor

    lte_rrc_analyzer = LteRrcAnalyzer()
    lte_rrc_analyzer.set_source(src)  # bind with the monitor

    # wcdma_rrc_analyzer = WcdmaRrcAnalyzer()
    # wcdma_rrc_analyzer.set_source(src)  # bind with the monitor

    # lte_nas_analyzer = LteNasAnalyzer()
    # lte_nas_analyzer.set_source(src)

    # umts_nas_analyzer = UmtsNasAnalyzer()
    # umts_nas_analyzer.set_source(src)

    # lte_mac_analyzer = LteMacAnalyzer()
    # lte_mac_analyzer.set_source(src)

    # lte_meas_analyzer = LteMeasurementAnalyzer()
    # lte_meas_analyzer.set_source(src)

    # print lte_meas_analyzer.get_rsrp_list() 
    # print lte_meas_analyzer.get_rsrq_list()

    # Start the monitoring
    src.run()