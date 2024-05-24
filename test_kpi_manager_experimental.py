from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer.kpi import KPIManager, KpiAnalyzer
import cProfile

if __name__ == '__main__':
    src = SparkReplayer()
    src.set_input_path("./logs/bler_sample.mi2log")

    kpi_manager = KPIManager()

    # Test experimental KPIs - data plane
    kpi_manager.enable_kpi("KPI.Wireless.BLER") # test log: bler_sample
    kpi_manager.enable_kpi("KPI.Wireless.DL_PDCP_LOSS") # test log: data_sample
    kpi_manager.enable_kpi("KPI.Wireless.UL_PDCP_LOSS")

    # Test experimental KPIs - handover
    kpi_manager.enable_kpi("KPI.Mobility.HANDOVER_PREDICTION") # test log: data_sample
    kpi_manager.enable_kpi("KPI.Mobility.HANDOVER_LATENCY") # test log: data_sample
    kpi_manager.enable_kpi("KPI.Mobility.HANDOVER_HOL") # test log: data_sample

    kpi_manager.set_source(src)

    src.run()