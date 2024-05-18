#!/usr/bin/env python3
from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer import NrRrcAnalyzer

def main():
    src = SparkReplayer()
    src.set_input_path("./logs")

    src.enable_log("LTE_RLC_UL_Stats")

    src.save_log_as("./output")
    # nr_rrc_analyzer = NrRrcAnalyzer()
    # nr_rrc_analyzer.set_source(src)  # bind with the monitor

    src.run()


if __name__ == '__main__':
    main()
