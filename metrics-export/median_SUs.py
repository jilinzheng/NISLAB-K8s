"""
Query Prometheus HTTP API for median Service Units
"""

import requests
from datetime import datetime
import pandas as pd
import statistics

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# start and end times of test result range
START_TIME = '1733858400'      # specify unix start time
END_TIME = '1733862000'        # specify end time
EXPORT_FILENAME = 'testMedian.csv'
TIMEFRAME = "1m"

# get the container cpu usage per pod
params={"query":
        f"""
        ceil(
        sum(rate(container_cpu_usage_seconds_total{{namespace="default"}}[{TIMEFRAME}])) >
        sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024)) or
        sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024))
        )
        """,
        "start":
        f'{START_TIME}',
        "end":
        f'{END_TIME}',
        "step":
        f"{TIMEFRAME}"
}
res = requests.get(PROM_QUERY_RANGE_API, params=params).json()
res_values = res['data']['result'][0]['values']
timestamps, service_units = [], []
for value in res_values:
    timestamp = value[0]
    timestamps.append(datetime.fromtimestamp(timestamp))
    service_units.append(float(value[1]))

print(f"MEDIAN: {statistics.median(service_units)}")

# create dataframe + write to csv
df = pd.DataFrame({
    'Timestamp': timestamps,
    'Service Units': service_units
})
# df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
df.to_csv(f'./{EXPORT_FILENAME}',index=False)