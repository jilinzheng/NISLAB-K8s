"""
Query Prometheus HTTP API for specified metrics
"""


import requests
import time
from datetime import datetime
import pandas as pd


# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"


# get the cumulative container cpu usage 
params={"query":
        "sum(rate(container_cpu_usage_seconds_total{namespace='default'}[1m])) by (pod)",
        "start":
        f"{int(time.time()) - 3600}", # time from one hour ago
        #1714534800,                  # unix time
        "end":
        f"{int(time.time())}", # time now
        #1714535700,           # unix time
        "step":
        "1m"
}
res = requests.get(PROM_QUERY_RANGE_API, params=params).json()


# extract desired data: podname, timestamp, and usage value
res_data = res['data']['result']
pods, timestamps, values = [], [], []
for pod in res_data:
    pod_name = pod['metric']['pod']
    first_entry = True
    for timestamp, value in pod['values']:
        if first_entry:
            pods.append(pod_name)
            first_entry = False
        else:
            pods.append('')
        timestamps.append(datetime.fromtimestamp(timestamp))
        values.append(float(value))


# create dataframe + write to excel
df = pd.DataFrame({
    'Pod': pods,
    'Timestamp': timestamps,
    'Value': values
})
df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
