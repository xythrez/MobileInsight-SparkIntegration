#!/usr/bin/python
"""
kpi_analyzer_custom.py

Authors: Karl Goeltner and Shrea Chari
"""

from mobile_insight_dev.analyzer.track_cell_info_analyzer_custom import CustomTrackCellInfoAnalyzer
from mobile_insight.analyzer.analyzer import Analyzer

is_android = False
try:
    from jnius import autoclass  # For Android
    try:
        from service import mi2app_utils 
        PythonService = autoclass('org.kivy.android.PythonService')
        pyService = PythonService.mService    
        Context = autoclass('android.content.Context')
        ConnectivityManager = pyService.getSystemService(Context.CONNECTIVITY_SERVICE)   
    except Exception as e:
        import main_utils
    is_android = True
except Exception as e:
    is_android = False

__all__ = ["CustomKPIAnalyzer"]

import os, errno
import urllib.request, urllib.error, urllib.parse, json, time, datetime
import threading
from collections import deque

class CustomKPIAnalyzer(Analyzer):

    # Global variables: For asynchrounous KPI upload
    upload_thread = None
    pending_upload_task = deque([]) # (kpi_name, kpi_val) pair list

    @classmethod
    def spark_export(cls, analyzer):
       logs = analyzer.get_logs() 
       return json.dumps(logs)

    @classmethod
    def spark_collect(cls, list_of_results):
        combined_logs = []
        for result in list_of_results:
            logs = json.loads(result) 
            combined_logs.extend(logs)
        
        # save logs in a file and return file name
        with open('combined_logs.json', 'w') as file:
            json.dump(combined_logs, file)
        
        return 'combined_logs.json'

    def __init__(self):

        Analyzer.__init__(self)

        # use custom trackcellinfoanalyzer for spark case
        if "CustomTrackCellInfoAnalyzer" not in Analyzer._Analyzer__analyzer_array:
            Analyzer._Analyzer__analyzer_array["CustomTrackCellInfoAnalyzer"] = CustomTrackCellInfoAnalyzer()
            self.include_analyzer('CustomTrackCellInfoAnalyzer', [])
        else:
            self.include_analyzer('CustomTrackCellInfoAnalyzer', [])

        # initilize local database
        self.supported_kpis = {} # Supported KPIs: kpi_name -> callback
        # self.__db = None # Local dabatase: kpi_name -> database
        # self.__conn = None # Local database cursor: kpi_name -> database
        self.kpi_files = {}
        self.__op = ""
        self.__phone_model = ""
        # self.__db_enabled = False
        self.__periodicity = {}
        self.__logcell = {}
        self.__last_updated = {}

        # Initialize uploading thread
        if is_android and not CustomKPIAnalyzer.upload_thread:
            e = threading.Event()
            CustomKPIAnalyzer.upload_thread = threading.Thread(target=self.__upload_kpi_thread, args=(e,))
            CustomKPIAnalyzer.upload_thread.start()

    def __del__(self):
        if is_android:
            mi2app_utils.detach_thread()

    def get_logs(self):
        directory_path='./kpis/'
        combined_data = []  # Initialize an empty list to store all the logs

        # List all files in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):  # Check if the file is a JSON file
                file_path = os.path.join(directory_path, filename)
                with open(file_path, 'r') as file:
                    data = json.load(file)  # Load the JSON data from the file
                    if isinstance(data, list):
                        combined_data.extend(data)  # Extend the list if the data is a list
                    else:
                        combined_data.append(data)  # Append the data if it is a dictionary

        return combined_data

    def enable_local_storage(self, enable_storage):
        """
        Set if the local KPI should be stored

        :param enable_storage: Whether to locally store the kpi. False by default
        :type enable_storage: boolean
        """
        #self.__db_enabled = enable_storage
        pass

    def register_kpi(self, kpi_type, kpi_name, callback, attributes = None):
        if kpi_name in self.supported_kpis:
            return False
        
        self.supported_kpis[kpi_name] = callback
        # Ensure JSON file for each KPI exists
        file_path = f'./kpis/{kpi_name}.json'
        self.kpi_files[kpi_name] = file_path

        if not os.path.exists(file_path):
            with open(file_path, 'w') as file:
                json.dump([], file)
        return True


    def __create_table(self, kpi_name, attributes):
        return None
    
    def __create_db(self):
        return None


    def list_kpis(self):
        """
        Return a list of available KPIs 

        :returns: a list of string, each of which is a KPI name
        """
        return list(self.supported_kpis.keys())

    def __db_query(self, sql_cmd):
        """
        Return query result of a sql_cmd
        """
        return None

    def count_entries_before_timestamp(self, data, kpi_key, timestamp=None):
        """
        Count the number of entries for a specific KPI before a given timestamp.

        :param data: List of dictionaries loaded from a JSON file.
        :param kpi_key: The key in the 'value' dictionary to count.
        :param timestamp: If provided, counts entries before this datetime; otherwise, counts all entries.
        :type timestamp: datetime, optional
        :return: Count of entries meeting the criteria.
        """
        count = 0
        if timestamp:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            for entry in data:
                entry_timestamp = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
                if entry_timestamp < timestamp:
                    count += 1
        else:
            for entry in data:
                count += 1

        return count

    def local_query_kpi(self, kpi_name, cell_id = None, timestamp = None):
        """
        Query the phone's locally observed KPI

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param cell_id: cell global id
        :type cell_id: string
        :param timestamp: The timestamp of the KPI. If None, this function returns the latest KPI
        :type timestamp: datetime
        :returns: The KPI value, or None if the KPI is not available
        """
        if kpi_name not in self.kpi_files:
            return None
        with open(self.kpi_files[kpi_name], 'r') as file:
            data = json.load(file)
            
            
        if kpi_name.endswith('SR'):
            if cell_id is None:
                if 'HO' in kpi_name:
                    kpi_suc = kpi_name[:-2]+'FAILURE'
                else:
                    kpi_suc = kpi_name[:-2]+'SUC'
                    
                # check if this file exists
                try:
                    with open(f"./kpis/{kpi_suc}.json", 'r') as file:
                        data_suc = json.load(file)
                except FileNotFoundError:
                    self.log_warning(f"No data file found for {kpi_suc}")
                    return None
                
                # Count successful entries
                suc_num = self.count_entries_before_timestamp(data_suc, kpi_suc, timestamp)

                if 'HO' in kpi_name:
                    kpi_req = kpi_name[:-2]+'TOTAL'
                else:
                    kpi_req = kpi_name[:-2]+'REQ'
                
                # check if this file exists
                try:
                    with open(f"./kpis/{kpi_req}.json", 'r') as file:
                        data_req = json.load(file)
                except FileNotFoundError:
                    self.log_warning(f"No data file found for {kpi_req}")
                    return None
                
                # Count total requests or attempts
                req_num = self.count_entries_before_timestamp(data_req, kpi_req, timestamp)

            # print suc_num, req_num

            if req_num and suc_num and req_num > 0:
                if 'HO' in kpi_name:
                    success_rate = (req_num - suc_num) / req_num * 100
                else:
                    success_rate = suc_num / req_num * 100
                return '{:.2f}%'.format(success_rate)

            return None

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
        if kpi_name not in self.kpi_files:
            return None
        with open(self.kpi_files[kpi_name], 'r') as file:
            data = json.load(file)
        return data      


    def set_periodicity(self, kpi_showname, periodicity):
        """
        Set periodicity of the analyzer

        :param kpi_showname: The KPI to be queried, this is the showname
        :type kpi_showname: string
        :param periodicity: periodicity (s,m,h,d repsents scale of seconds, minutes, hours, days)
        :type periodicity: string
        """
        try:
            kpi_name = kpi_showname.replace('.', '_')
            if periodicity.isdigit():
                self.__periodicity[kpi_name] = int(periodicity)
            elif periodicity.endswith('s'):
                self.__periodicity[kpi_name] = int(periodicity[:-1])
            elif periodicity.endswith('m'):
                self.__periodicity[kpi_name] = int(periodicity[:-1])*60
            elif periodicity.endswith('h'):
                self.__periodicity[kpi_name] = int(periodicity[:-1])*60*60
            elif periodicity.endswith('d'):
                self.__periodicity[kpi_name] = int(periodicity[:-1])*60*60*24
            self.__last_updated[kpi_name] = None
            self.log_info("Priority set for "+kpi_showname+': '+periodicity)
            return True
        except:
            self.log_info("Priority set failed for "+kpi_showname+': '+periodicity)
            return False

    def set_cell(self, kpi_showname, cell):
        """
        Set periodicity of the analyzer

        :param kpi_showname: The KPI to be queried, this is the showname
        :type kpi_showname: string
        :param cell: cell (s,m,h,d repsents scale of seconds, minutes, hours, days)
        :type cell: string
        """
        try:
            kpi_name = kpi_showname.replace('.', '_')
            self.__logcell[kpi_name] = cell
            self.log_info("Logging cell set for "+kpi_showname+': '+str(cell))
            return True
        except:
            self.log_info("Logging cell failed for "+kpi_showname+': '+periodicity)
            return False


    def store_kpi(self, kpi_name, kpi_value, timestamp, cur_location=None):
        """
        Store the KPIs to the local database

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param kpi_value: The value of KPI or a dict {attribute <type: str>: value <type: str>}
        :type kpi_value: string
        :param timestamp
        :type timestamp: datetime
        """
        # manual mocking to adapt to custom attach_suc
        if kpi_name == "KPI_Accessibility_ATTACH_SUC":
            kpi_name = "ATTACH_SUC"
        if kpi_name == "KPI_Accessibility_ATTACH_REQ":
            kpi_name = "ATTACH_REQ"

        if kpi_name not in self.kpi_files:
            self.log_info(f"KPI {kpi_name} not registered.")
            return False
        file_path = self.kpi_files[kpi_name]
        with open(file_path, 'r+') as file:
            data = json.load(file)
            data.append({'value': kpi_value, 'timestamp': str(timestamp)})
            file.seek(0)
            json.dump(data, file, indent=4)

        cell_id = self.get_analyzer('CustomTrackCellInfoAnalyzer').get_cur_cell_id()
        self.__log_kpi(kpi_name, timestamp, cell_id, kpi_value)

    def __log_kpi(self, kpi_name, timestamp, cell_id, kpi_value):
        """
        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param timestamp
        :type timestamp: datetime
        :param cell_id: updated kpi cell id
        :type cell_id: string
        """

        if kpi_name in self.__last_updated:
            # if logging cell is specified, check whether cell id are the same
            if not self.__logcell[kpi_name] or self.__logcell[kpi_name] and self.__logcell[kpi_name] == str(cell_id):
                kpi_showname = kpi_name.replace('_', '.')
                # if periodicity mode enabled, check whether time gap is longer enough
                if not self.__last_updated[kpi_name] or (timestamp - self.__last_updated[kpi_name]).total_seconds() > self.__periodicity[kpi_name]:
                    self.__last_updated[kpi_name] = timestamp
                    if kpi_name.endswith('_LOSS') or kpi_name.endswith('_BLER'):
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=' + str(kpi_value) + '%')
                    elif kpi_name.endswith('_TPUT'):
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=' + str(kpi_value) + 'bps')
                    elif kpi_name.endswith('_LATENCY') or kpi_name.endswith('_HOL'):
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=' + str(kpi_value) + 'ms')
                    elif kpi_name.endswith('_PREDICTION'):
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=Triggered')
                    else:
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=' + str(self.local_query_kpi(kpi_name)))

        # check the stats updated with instance value
        if kpi_name.endswith('SUC') or kpi_name.endswith('FAILURE'):
            kpi_name=kpi_name.replace('SUC', 'SR')
            kpi_name=kpi_name.replace('FAILURE', 'SR')
            if kpi_name in self.__last_updated:
                if not self.__logcell[kpi_name] or self.__logcell[kpi_name] and self.__logcell[kpi_name] == str(cell_id):
                    kpi_showname = kpi_name.replace('_', '.')
                    if not self.__last_updated[kpi_name] or (timestamp - self.__last_updated[kpi_name]).total_seconds() > self.__periodicity[kpi_name]:
                        self.__last_updated[kpi_name] = timestamp
                        kpi_showname = kpi_name.replace('_', '.')
                        self.log_info(str(timestamp) + ': '+ str(kpi_showname) + '=' + str(self.local_query_kpi(kpi_name)))

    def __upload_kpi_thread(self,e):
        """
        Internal thread to upload the KPI
        """

        while True:
            if CustomKpiAnalyzer.pending_upload_task:
                while True:
                    activeNetworkInfo = ConnectivityManager.getActiveNetworkInfo()
                    if activeNetworkInfo and activeNetworkInfo.isConnected():
                        break
                    e.wait(1)

                while CustomKpiAnalyzer.pending_upload_task:
                    item = CustomKpiAnalyzer.pending_upload_task.popleft()
                    # self.__upload_kpi_async(item[0],item[1])
                    while not self.__upload_kpi_async(item[0],item[1],item[2]):
                        e.wait(5)
            e.wait(5)

    def __upload_kpi_async(self,kpi_name, kpi_value, cur_location):
        """
        Upload the KPI value to the cloud

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param kpi_value: The value of KPI
        :type kpi_value: string
        """
        self.log_debug("uploading kpi: "+kpi_name)
        return True

    def upload_kpi(self,kpi_name, kpi_value):
        """
        Upload the KPI value to the cloud

        :param kpi_name: The KPI to be queried
        :type kpi_name: string
        :param kpi_value: The value of KPI
        :type kpi_value: string
        """
        # self.log_info("New KPI: " + kpi_name)
        cur_location = self.__get_current_gps()
        CustomKpiAnalyzer.pending_upload_task.append((kpi_name,kpi_value,cur_location))
        
    def __get_phone_model(self):
        if is_android:
            #TODO: Optimization, avoid repetitive calls
            res = mi2app_utils.get_phone_manufacturer()+"-"+mi2app_utils.get_phone_model()
            # self.log_debug("Phone model: "+res)
            return res
        else:
            return self.__phone_model

    def __get_operator_info(self):
        if is_android:
            #TODO: Optimization, avoid repetitive calls
            return mi2app_utils.get_operator_info()
        else:
            self.__op = self.get_analyzer('TrackCellInfoAnalyzer').get_cur_op()
            return self.__op

    def __get_current_gps(self):
        if is_android:
            location = mi2app_utils.get_current_location()
            # self.log_debug("Current location: "+str(location)) 
            return location
        else:
            return ""

    def set_phone_model(self, phone_model):
        """
        Set phone model
        :param phone_model: string
        :return:
        """
        self.__phone_model = phone_model

    def set_operator(self, operator):
        """
        Set operator
        :param operator: string
        :return:
        """
        self.__op = operator