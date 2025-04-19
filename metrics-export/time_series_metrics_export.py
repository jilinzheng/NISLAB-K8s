"""
Query Prometheus HTTP API for
- service units and median service units over time
- rate of total, successful, and failed requests over time
and writes the time series data out to a .csv.
"""

import requests
from datetime import datetime
import pandas as pd
import os

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# tests-specific data
SCENARIOS = [
    "bursty-sliding-window-5x",
    "bursty-sliding-window-10x",
    "bursty-sliding-window-20x",
]
START_TIMES = [
    "1743553485533",
    "1743561323198",
    "1743569150891",
]  # unix ms
END_TIMES = [
    "1743560686115",
    "1743568523510",
    "1743576351226",
]  # unix ms
TIMEFRAMES = ["1m", "5m", "1h"]


def query_rate_of_total_requests(timeframe):
    return f"""sum(rate(istio_requests_total{{destination_service_name="teastore-webui"}}[{timeframe}])) by (destination_service)"""


def query_rate_of_successful_requests(timeframe):
    return f"""sum(rate(istio_requests_total{{destination_service_name="teastore-webui",response_code=~"[23]\\\\d{{2}}"}}[{timeframe}]))"""


def query_rate_of_failed_requests(timeframe):
    return f"""sum(rate(istio_requests_total{{destination_service_name="teastore-webui",response_code=~"(0|[45]\\\\d{{2}})"}}[{timeframe}]))"""


def query_service_units_used(timeframe):
    return f"""
    ceil(
        max(
            sum(rate(container_cpu_usage_seconds_total{{namespace="default"}}[{timeframe}])) >
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024)) or
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024))
        )
    )
    """


def query_median_service_units_used(timeframe):
    return f"""median_service_units_{timeframe}"""


QUERIES = [
    (query_rate_of_total_requests, "Rate of Total Requests"),
    (query_rate_of_successful_requests, "Rate of Successful Requests"),
    (query_rate_of_failed_requests, "Rate of Failed Requests"),
    (query_service_units_used, "Service Units Used"),
    (query_median_service_units_used, "Median Service Units Used"),
]

if (
    len(START_TIMES) != len(END_TIMES)
    or len(START_TIMES) != len(SCENARIOS)
    or len(SCENARIOS) != len(END_TIMES)
):
    raise ValueError("CONSTANTS length mismatch!")

for i in range(len(SCENARIOS)):
    # create directory for the specific scenario
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_dir_path = os.path.join(
        script_dir, f"250402_metrics_export_{SCENARIOS[i]}"
    )
    os.mkdir(scenario_dir_path)
    for j in range(len(TIMEFRAMES)):
        for k in range(len(QUERIES)):
            params = {
                "query": f"{QUERIES[k][0](TIMEFRAMES[j])}",
                "start": f"{float(START_TIMES[i])/1000.0}",
                "end": f"{float(END_TIMES[i])/1000.0}",
                "step": "15s",
            }
            res = requests.get(PROM_QUERY_RANGE_API, params=params).json()

            # extract desired data
            values = res["data"]["result"][0]["values"]
            timestamps, target_values = [], []
            for value in values:
                timestamp = value[0]
                timestamps.append(datetime.fromtimestamp(timestamp))
                target_values.append(value[1])

            # create dataframe + write to csv
            filename = f"{scenario_dir_path}/250402_{SCENARIOS[i]}_{QUERIES[k][1].replace(' ','_').lower()}_{TIMEFRAMES[j]}.csv"
            df = pd.DataFrame(
                {"Timestamp": timestamps, f"{QUERIES[k][1]}": target_values}
            )
            df.to_csv(filename, index=False)
            print(f"{filename} successfully written!")
