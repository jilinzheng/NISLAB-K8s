"""
Query Prometheus HTTP API for
- rate of total, successful, and failed requests over time
- service units and median service units over time
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
    "random_sliding_window_5x",
    "random_sliding_window_10x",
    "random_sliding_window_20x",
    "random_yoyo_5x",
    "random_yoyo_10x",
    "random_yoyo_20x",
    "random_state_aware_5x",
    "random_state_aware_10x",
    "random_state_aware_20x",
    "onoff_yoyo_5x",
    "onoff_yoyo_10x",
    "onoff_yoyo_20x",
    "onoff_yoyo_overlap_5x",
    "onoff_yoyo_overlap_10x",
    "onoff_yoyo_overlap_20x",
    "onoff_state_aware_5x",
    "onoff_state_aware_10x",
    "onoff_state_aware_20x",
    "onoff_sliding_window_5x",
    "onoff_sliding_window_10x",
    "onoff_sliding_window_20x",
    "bursty_yoyo_5x",
    "bursty_yoyo_10x",
    "bursty_yoyo_20x",
    "bursty_state_aware_5x",
    "bursty_state_aware_10x",
    "bursty_state_aware_20x",
    "bursty_sliding_window_5x",
    "bursty_sliding_window_10x",
    "bursty_sliding_window_20x",
]
START_TIMES = [
    "1742781608043",
    "1742789456778",
    "1742797306677",
    "1742878686769",
    "1742886538266",
    "1742894390353",
    "1742902247352",
    "1742910100518",
    "1742930333252",
    "1743043038169",
    "1743050896694",
    "1743058764379",
    "1743066631078",
    "1743074488652",
    "1743100041342",
    "1743107900999",
    "1743115739883",
    "1743123579079",
    "1743131418907",
    "1743139272535",
    "1743147130075",
    "1743263110222",
    "1743156797898",
    "1743164648098",
    "1743172507863",
    "1743180359450",
    "1743188220509",
    "1743196103030",
    "1743203954212",
    "1743211811056",
]  # unix ms
END_TIMES = [
    "1742788806535",
    "1742796654596",
    "1742804501372",
    "1742885887096",
    "1742893738595",
    "1742901590647",
    "1742909445514",
    "1742917300800",
    "1742937533497",
    "1743050238535",
    "1743058097180",
    "1743065964893",
    "1743073831505",
    "1743081689148",
    "1743107241945",
    "1743115101141",
    "1743122940022",
    "1743130779215",
    "1743138619110",
    "1743146472729",
    "1743154330271",
    "1743270310520",
    "1743163998210",
    "1743171849251",
    "1743179708188",
    "1743187559743",
    "1743195420731",
    "1743203303239",
    "1743211154423",
    "1743219011273",
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
        script_dir, f"250329_metrics_export_{SCENARIOS[i]}"
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
            filename = f"{scenario_dir_path}/250329_{SCENARIOS[i]}_{QUERIES[k][1].replace(' ','_').lower()}_{TIMEFRAMES[j]}.csv"
            df = pd.DataFrame(
                {"Timestamp": timestamps, f"{QUERIES[k][1]}": target_values}
            )
            # df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
            df.to_csv(filename, index=False)
            print(f"{filename} successfully written!")
