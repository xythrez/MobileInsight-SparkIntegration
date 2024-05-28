from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer import LteDlRetxAnalyzer

def collect_func(items):
  stats_list = {'mac_delay':0.0, 'mac_delay_sample':0, 'rlc_delay':0.0, 'rlc_delay_sample':0}
  for result in items:
    for _, bearer in result.bearer_entity.items():
      for item in bearer.mac_retx:
        stats_list['mac_delay'] += item['mac_retx']
      stats_list['mac_delay_sample'] += len(bearer.mac_retx)

      for item in bearer.rlc_retx:
        stats_list['rlc_delay'] += item['rlc_retx']
      stats_list['rlc_delay_sample'] += len(bearer.rlc_retx)
  return stats_list

if __name__ == "__main__":
    src = SparkReplayer()
    src.set_input_path('./logs')

    lteAnalyzer = LteDlRetxAnalyzer()
    lteAnalyzer.set_source(src)
    src.set_analyzer_callbacks(lteAnalyzer, spark_collect=collect_func)
    src.run()
    stats_list = lteAnalyzer.collect()

    avg_mac_delay = float(stats_list['mac_delay']) / stats_list['mac_delay_sample'] if stats_list['mac_delay_sample'] > 0 else 0.0
    avg_rlc_delay = float(stats_list['rlc_delay']) / stats_list['rlc_delay_sample'] if stats_list['rlc_delay_sample'] > 0 else 0.0

    print("Average MAC retx delay is:", avg_mac_delay)
    print("Average RLC retx delay is:", avg_rlc_delay)