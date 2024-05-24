from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight.analyzer.kpi import KPIManager, KpiAnalyzer
import cProfile

if __name__ == '__main__':
    src = SparkReplayer()
    src.set_input_path("./logs/volte_sample.mi2log")

    kpi_manager = KPIManager()

    # enable specific kpis: general, mobility, retainability, integirty
    kpi_manager.enable_kpi("KPI.Accessibility.DEDICATED_BEARER_SR_QCI1_REQ", periodicity='10m')
    kpi_manager.enable_kpi("KPI.Accessibility.DEDICATED_BEARER_SR_QCI1_SR", periodicity='2h')
    kpi_manager.enable_kpi("KPI.Accessibility.RRC_SUC")
    kpi_manager.enable_kpi("KPI.Accessibility.RRC_SR", cell='22205186')
    # kpi_manager.enable_kpi("KPI.Accessibility.SR_SUC", periodicity='1h')
    kpi_manager.enable_kpi("KPI.Accessibility.SR_SR", periodicity='1h')
    # kpi_manager.enable_kpi("KPI.Accessibility.ATTACH_SUC")
    kpi_manager.enable_kpi("KPI.Accessibility.ATTACH_SR")

    # Test Mobility KPIs
    # kpi_manager.enable_kpi("KPI.Mobility.HO_TOTAL")
    kpi_manager.enable_kpi("KPI.Mobility.HO_SR")
    # kpi_manager.enable_kpi("KPI.Mobility.HO_TOTAL", periodicity='1h')
    # kpi_manager.enable_kpi("KPI.Mobility.HO_FAILURE", periodicity='1h')
    kpi_manager.enable_kpi("KPI.Mobility.TAU_SR", periodicity='1h')
    # kpi_manager.enable_kpi("KPI.Mobility.TAU_REQ", periodicity='1h')

    # Test Retainability KPIs
    kpi_manager.enable_kpi("KPI.Retainability.RRC_AB_REL") 

    # Test Integrity KPIs
    kpi_manager.enable_kpi("KPI.Integrity.DL_TPUT") 

    kpi_manager.set_source(src)

    src.run()