"""Query Prometheus HTTP API for specified metrics, and convert the json response into a csv file."""

import json
import requests
import pandas as pd
from flatten_json import flatten

# Get json responses from Prometheus HTTP API
prom_api = "http://localhost:30000/api/v1/query"
pod_response = requests.get(prom_api, params={"query": "rate(container_cpu_usage_seconds_total{image='docker.io/library/nginx:latest'}[5m])"}).json()
cluster_response = requests.get(prom_api, params={"query": "sum (rate (container_cpu_usage_seconds_total{id='/'}[1m])) / sum (machine_cpu_cores) * 100"}).json()

# Write json data to a json file to verify proper response
with open("pod_response.json", 'w') as json_file:
    json.dump(pod_response, json_file, indent=4)
with open("cluster_response.json", 'w') as json_file:
    json.dump(cluster_response, json_file, indent=4)

# Convert pod usage json to csv
with open("pod_response.json", "r", encoding="utf8") as f:
    pod_json = json.load(f)
    pod_json = flatten(pod_json)

    # Convert flattened json to csv
    pd_dataframe = pd.Series(pod_json).to_frame()
    pd_dataframe.to_csv("pod_response.csv", index=True)

# Convert cluster usage json to csv
with open("cluster_response.json", "r", encoding="utf8") as f:
    cluster_json = json.load(f)
    cluster_json = flatten(cluster_json)
    pd_dataframe = pd.Series(cluster_json).to_frame()
    pd_dataframe.to_csv("cluster_response.csv", index=True)
