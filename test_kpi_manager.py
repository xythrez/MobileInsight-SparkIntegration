from mobile_insight_dev.monitor import SparkReplayer
from mobile_insight_dev.analyzer.kpi_manager_custom import CustomKPIManager
from mobile_insight_dev.analyzer.track_cell_info_analyzer_custom import CustomTrackCellInfoAnalyzer
from mobile_insight_dev.analyzer.kpi_analyzer_custom import CustomKPIAnalyzer
from mobile_insight_dev.analyzer.attach_sr_analyzer_custom import CustomAttachSrAnalyzer
from mobile_insight.analyzer.analyzer import Analyzer

## test script for KPI Manager
if __name__ == '__main__':
    src = SparkReplayer()
    # src.set_input_path("./logs/attach_sample.mi2log")     # single log 
    src.set_input_path("./logs/attach_samples")    # multiple logs

    # use new customKPIManager
    kpi_manager = CustomKPIManager()

    # enable one specific kpi: functionality only adapted for ATTACH_SR
    kpi_manager.enable_kpi("KPI.Accessibility.ATTACH_SR")

    # connect customKPIManager to sparkReplayer
    kpi_manager.set_source(src)

    src.run()
