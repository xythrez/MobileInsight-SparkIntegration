import os
import timeit
import dill as pickle
import pandas as pd

from mobile_insight.monitor import OfflineReplayer
from mobile_insight.element import Event

class SparkSubmonitor(OfflineReplayer):
    '''Internal per-task sub-monitor

    Do not use this class directly
    '''

    def __init__(self, analyzer_info):
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

    def run(self, data):
        results = {}

        # Dispatch events
        for _, row in data.iterrows():
            packet = pickle.loads(row['packet'])
            event = (timeit.default_timer(), row['type_id'], packet)
            self.send(event)

        # Collect results - serialize the result obj
        for analyzer_id, tup in self.analyzers.items():
            results[analyzer_id] = pickle.dumps(tup[1](tup[0]))

        return pd.DataFrame([(1, results)])
