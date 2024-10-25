"""
Query Prometheus HTTP API for specified metrics
"""

import requests
from datetime import datetime
import pandas as pd

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# start and end times of test result range
START_TIME = '1729299876'      # specify unix start time
END_TIME = '1729310683'        # specify end time
EXPORT_FILENAME = '241018_cust_delay_const_attk_7.5x_3h_v3.csv'

# get the container cpu usage per pod
params={"query":
        """ceil(
                max(
                    sum(rate(container_cpu_usage_seconds_total{namespace="default"}[1m])) or
                    sum(container_memory_working_set_bytes{namespace='default'} / (4 * 1024 * 1024 * 1024))
                )
            )""",
        "start":
        f'{START_TIME}',
        "end":
        f'{END_TIME}',
        "step":
        "1m"
}
res = requests.get(PROM_QUERY_RANGE_API, params=params).json()

# extract desired data: max service units by the minute
max_service_unit_values = res['data']['result'][0]['values']
timestamps, max_service_units = [], []
for value in max_service_unit_values:
    timestamp = value[0]
    timestamps.append(datetime.fromtimestamp(timestamp))
    max_service_units.append(value[1])

# create dataframe + write to csv
df = pd.DataFrame({
    'Timestamp': timestamps,
    'Max Service Units': max_service_units
})
# df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
df.to_csv(f'./{EXPORT_FILENAME}',index=False)