from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer.msg_statistics import MsgStatistics

"""
This example shows how to get basic statistics of a offline log
"""
if __name__ == "__main__":

    # Initialize a 3G/4G monitor
    src = SparkReplayer()
    src.set_input_path("./logs")

    statistics = MsgStatistics()
    statistics.set_source(src)

    # Start the monitoring
    src.run()
    all_statistics = statistics.collect()

    # Save results
    f_statistics = open('./msg_type_statistics.txt', 'w')
    for stats in all_statistics:
        for item in stats.msg_type_statistics:
            f_statistics.write(
                item + " " + str(stats.msg_type_statistics[item]) + "\n")
    f_statistics.close()

    f_rate = open('./msg_arrival_rate.txt', 'w')
    for stats in all_statistics:
        for item in stats.msg_arrival_rate:
            f_rate.write(item + " ")
            for k in range(1, len(stats.msg_arrival_rate[item])):
                f_rate.write(str(
                    (stats.msg_arrival_rate[item][k] - stats.msg_arrival_rate[item][k - 1]).total_seconds() * 1000) + " ")
            f_rate.write("\n")
    f_rate.close()

    f_msg_len = open('./msg_length.txt', 'w')
    for stats in all_statistics:
        for item in stats.msg_lengh:
            f_msg_len.write(item + " ")
            for k in range(0, len(stats.msg_lengh[item])):
                f_msg_len.write(str(stats.msg_lengh[item][k]) + " ")
            f_msg_len.write("\n")
    f_msg_len.close()
