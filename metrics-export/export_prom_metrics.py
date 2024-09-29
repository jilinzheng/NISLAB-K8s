"""
Query Prometheus HTTP API for specified metrics, and convert the json response into a csv file.
"""


import time
import json
import requests
import pandas as pd
from flatten_json import flatten

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://localhost:32000/api/v1/query"
PROM_QUERY_RANGE_API = "http://localhost:32000/api/v1/query_range"


# Get the cumulative container cpu usage 
params={"query":
        "sum(rate(container_cpu_usage_seconds_total{namespace='default'}[1m])) by (pod)",
        "start":
        f"{int(time.time()) - 3600}", # time from one hour ago
        #1714534800,
        "end":
        f"{int(time.time())}", # time now
        #1714535700,
        "step":
        "1m"
}

prom_response = requests.get(PROM_QUERY_RANGE_API, params=params).json()

# Write json data to a json file to verify proper response
with open("prom_response.json", 'w') as json_file:
    json.dump(prom_response, json_file, indent=4)

# Convert pod usage json to csv
with open("prom_response.json", "r", encoding="utf8") as f:
    prom_json = json.load(f)
    prom_json = flatten(prom_json)

    # Convert flattened json to csv
    pd_dataframe = pd.Series(prom_json).to_frame()
    pd_dataframe.to_csv("prom_response.csv", index=True)
