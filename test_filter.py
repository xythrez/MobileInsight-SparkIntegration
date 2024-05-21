from mobile_insight_dev.monitor import SparkReplayer

if __name__ == "__main__":

    # Initialize a 3G/4G monitor
    src = SparkReplayer()
    src.set_input_path("./logs")
    # Save log as
    src.save_log_as("./output")

    # Configure the log to be saved
    src.enable_log("LTE_NAS_ESM_OTA_Incoming_Packet")
    src.enable_log("LTE_NAS_EMM_OTA_Incoming_Packet")

    # Start the monitoring
    src.run()