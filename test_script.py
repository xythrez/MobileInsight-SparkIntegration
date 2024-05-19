#!/usr/bin/env python3
from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer import LteMacAnalyzer

def main():
    src = SparkReplayer()
    src.set_input_path("./logs")

    src.save_log_as("./output")

    analyzer = LteMacAnalyzer()
    analyzer.set_source(src)  # bind with the monitor

    src.run()

    # New monkeypatching function. All analyzers registered with SparkReplayer
    # automatically get a new .collect() function that returns multiple
    # instances of itself containing the execution results.
    #
    # Register a collect_func using SparkReplayer.set_analyzer_callbacks() to
    # manually combine the results of each instance together
    print(analyzer.collect())


if __name__ == '__main__':
    main()
