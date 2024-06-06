#!/usr/bin/python
"""
kpi_manager_custom.py

Authors: Karl Goeltner and Shrea Chari
"""

from mobile_insight_dev.analyzer.kpi_analyzer_custom import CustomKPIAnalyzer
from mobile_insight_dev.analyzer.attach_sr_analyzer_custom import CustomAttachSrAnalyzer
from mobile_insight.analyzer.analyzer import Analyzer

import sys, inspect, os
import datetime


__all__ = ["CustomKPIManager"]


class CustomKPIManager(Analyzer):

    """
    An unified interface for users to track and query KPIs
    """
    supported_kpis={} # Supported KPIs: kpi_name -> KPIAnalyzer name

    def __init__(self):
        Analyzer.__init__(self)
        self.__check_kpis()



    def __check_kpis(self):

        """
        Find and include all supported KPIs into KPIManager.supported_kpis
        """
        module_tmp = __import__("mobile_insight")
        # print inspect.getmembers(module_tmp.analyzer.kpi,inspect.isclass)

        for item in inspect.getmembers(module_tmp.analyzer.kpi,inspect.isclass):
            if item[1].__bases__[0].__name__ ==  "KpiAnalyzer":
                # Mock only AttachSrAnalyzer object
                if item[0] == "AttachSrAnalyzer":
                    # avoid duplicate declarations of analyzers
                    if "CustomAttachSrAnalyzer" not in Analyzer._Analyzer__analyzer_array:
                        tmp_module = CustomAttachSrAnalyzer()
                    else:
                        tmp_module = Analyzer._Analyzer__analyzer_array["CustomAttachSrAnalyzer"]
                else:
                    tmp_module = item[1]()  # original analyzer initialization
                
                for kpi in tmp_module.list_kpis():
                    # add only CustomAttachSrAnalyzer name to kpi list
                    if kpi.startswith("ATTACH"):
                        CustomKPIManager.supported_kpis[kpi] = "CustomAttachSrAnalyzer"
                    else:
                        CustomKPIManager.supported_kpis[kpi] = item[0]
                    self.log_info(kpi)

        # manually enable kpi each time due to new Analyzer objects ran in Submonitor
        self.enable_kpi("KPI.Accessibility.ATTACH_SR")

    def list_kpis(self):
        """
        Return a list of available KPIs 

        :returns: a list of string, each of which is a KPI name
        """
        return list(self.supported_kpis.keys())

    def enable_all_kpis(self, enable_storage = False):
        """
        Enable all KPIs' monitoring
        
        :param enable_storage: Whether to locally store the kpi. False by default
        :type enable_storage: boolean
        """
        for kpi_name in self.list_kpis():
            self.enable_kpi(kpi_name, enable_storage)


    def enable_kpi(self, kpi_name, periodicity='0s', cell=None, enable_storage = True):
        """
        Enable the KPI monitoring

        :param kpi_name: The KPI to be monitored
        :type kpi_name: string
        :param enable_storage: Whether to locally store the kpi. False by default
        :type enable_storage: boolean
        :returns: True if successfully activated, False otherwise
        """

        # Mock original KPI attach_sr as custom attach_sr
        if kpi_name == "KPI.Accessibility.ATTACH_SR":
            kpi_name = "ATTACH_SR"

        if kpi_name not in self.supported_kpis:
            self.log_warning("KPI does not exist: "+kpi_name)
            return False

        try:
            kpi_analyzer_name = self.supported_kpis[kpi_name]

            # avoid duplicate declarations of analyzers
            if kpi_analyzer_name == "CustomAttachSrAnalyzer" and kpi_analyzer_name not in Analyzer._Analyzer__analyzer_array:
                Analyzer._Analyzer__analyzer_array[kpi_analyzer_name] = CustomAttachSrAnalyzer()
                self.include_analyzer(kpi_analyzer_name, [])
            else:
                self.include_analyzer(kpi_analyzer_name, [])

            # self.include_analyzer(kpi_analyzer_name, [])
            self.get_analyzer(kpi_analyzer_name).enable_local_storage(enable_storage)
            self.get_analyzer(kpi_analyzer_name).set_periodicity(kpi_name, periodicity)
            self.get_analyzer(kpi_analyzer_name).set_cell(kpi_name, cell)
            self.log_info("Enable KPI: "+kpi_name)
            return True
        except Exception as e:
            # Import failure
            self.log_warning("Fail to activate KPI: "+kpi_name)    
            return False


    def local_query_kpi(self, kpi_name, mode = 'cell', timestamp = None):
        """
        Query the phone's locally observed KPI

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param timestamp: The timestamp of the KPI. If None, this function returns the latest KPI
        :type timestamp: datetime
        :returns: The KPI value, or None if the KPI is not available
        """
        if kpi_name not in self.supported_kpis:
            self.log_warning("KPI does not exist: "+kpi_name)
            return None

        # if KPIManager.supported_kpi[kpi_name] not in 
        kpi_agent = self.get_analyzer(self.supported_kpis[kpi_name])
        if not kpi_agent:
            # KPI analyzer not triggered
            self.log_warning("KPI not activated yet: "+kpi_name)
            self.enable_kpi(kpi_name)
            return None

        return kpi_agent.local_query_kpi(kpi_name, mode, timestamp)

    def remote_query_kpi(self, kpi_name, phone_model, operator, gps, timestamp):
        """
        Query the remote cloud for the KPI

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param phone_model: The the phone model
        :type phone_model: string
        :param operator: The network operator
        :type operator: string
        :param gps: The GPS coordinate
        :type gps: string
        :param timestamp: The timestamp of the KPI. 
        :type timestamp: datetime
        :returns: The KPI value, or None if the KPI is not available
        """
        if kpi_name not in KPIManager.supported_kpis:
            self.log_warning("KPI does not exist: "+kpi_name)
            return None

        # if KPIManager.supported_kpi[kpi_name] not in 
        kpi_agent = self.get_analyzer(KPIManager.supported_kpi[kpi_name])
        if not kpi_agent:
            # KPI analyzer not triggered
            self.log_warning("KPI not activated yet: "+kpi_name)
            self.enable_kpi(kpi_name)
            return None

        return kpi_agent.local_query_kpi(kpi_name, phone_model, operator, gps, timestamp)