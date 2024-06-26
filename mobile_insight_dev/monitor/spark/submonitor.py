import os
import timeit
import dill as pickle
import pandas as pd

from mobile_insight.element import Event
from mobile_insight.analyzer import Analyzer
from mobile_insight.monitor import OfflineReplayer
from mobile_insight.monitor.dm_collector import (
    DMLogPacket,
)

class SparkSubmonitor(OfflineReplayer):
    '''Internal per-task sub-monitor

    Do not use this class directly
    '''

    def __init__(self, work_dir, analyzer_info):
        os.chdir(work_dir)
        Analyzer.reset()
        OfflineReplayer.__init__(self)
        self.analyzers = {}
        for analyzer_id, analyzer_cls, init_args, _, export_func in \
                analyzer_info:
            if isinstance(init_args, list):
                analyzer = analyzer_cls(*init_args)
            else:
                analyzer = analyzer_cls(*init_args())
            self.analyzers[analyzer_id] = (analyzer, export_func)
            analyzer.set_source(self)

    def enable_log(self, type_name):
        if isinstance(type_name, str):
            type_name = [type_name]
        for n in type_name:
            if n not in self._type_names:
                self._type_names.append(n)

    def run(self, data):
        results = {}

        # Dispatch events
        for _, row in data.iterrows():
            packet = DMLogPacket(pickle.loads(row['packet']))
            event = Event(timeit.default_timer(), row['type_id'], packet)
            self.send(event)

        # Collect results - serialize the result obj
        for analyzer_id, tup in self.analyzers.items():
            results[analyzer_id] = pickle.dumps(tup[1](tup[0]))

        return pd.DataFrame([(1, results)])
