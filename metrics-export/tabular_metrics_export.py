"""
Generate comma-separated values of max/median
customer-/attacker-phase Service Units used.
"""

import requests
import statistics

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# tests-specific data
SCENARIOS = [
    "bursty_sliding_window_5x",
    "bursty_sliding_window_10x",
    "bursty_sliding_window_20x",
]
START_TIMES = [
    "1743196103030",
    "1743203954212",
    "1743211811056",
]  # unix ms
END_TIMES = [
    "1743203303239",
    "1743211154423",
    "1743219011273",
]  # unix ms
TIMEFRAMES = [("1m", 60), ("5m", 300), ("1h", 3600)]  # seconds
ONE_HOUR_IN_S = 3600


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


# check each test scenario has matching start/end times
if (
    len(START_TIMES) != len(END_TIMES)
    or len(START_TIMES) != len(SCENARIOS)
    or len(SCENARIOS) != len(END_TIMES)
):
    raise ValueError("SCENARIOS/START_TIMES/END_TIMES length mismatch!")

# format output with column titles in first row
print("scenario, timeframe, max_cust, max_attk, med_cust, med_attk")
for i in range(len(SCENARIOS)):
    for j in range(len(TIMEFRAMES)):
        params = {
            "query": f"{query_service_units_used(TIMEFRAMES[j][0])}",
            "start": f"{float(START_TIMES[i])/1000.0}",
            "end": f"{float(END_TIMES[i])/1000.0}",
            "step": "5s",
        }
        res = requests.get(PROM_QUERY_RANGE_API, params=params).json()

        # extract desired data: service units
        values = res["data"]["result"][0]["values"]
        timestamps, target_values = [], []
        for value in values:
            timestamps.append(value[0])  # seconds
            target_values.append(value[1])  # SUs

        # split SUs into customer/attacker phases (1 hour per each phase)
        # only append if value is applicable within the same test
        # e.g., only include results at the 1-hour mark for the 1-hour timeframe,
        # e.g., only 30-minute and after for the 30-minute timeframe
        # a small 60-second buffer is added for 1h results to be appended
        customer_SUs, attacker_SUs = [], []
        for k in range(len(timestamps)):
            if (
                float(END_TIMES[i]) / 1000.0 - timestamps[k] >= ONE_HOUR_IN_S - 60
                and timestamps[k]
                >= float(START_TIMES[i]) / 1000.0 + TIMEFRAMES[j][1] - 60
            ):
                customer_SUs.append(int(target_values[k]))
            if (
                float(END_TIMES[i]) / 1000.0 - timestamps[k] <= ONE_HOUR_IN_S + 60
                and timestamps[k]
                >= float(START_TIMES[i]) / 1000.0
                + ONE_HOUR_IN_S
                + TIMEFRAMES[j][1]
                - 60
            ):
                attacker_SUs.append(int(target_values[k]))

        # print all column-title corresponding data in subsequent rows;
        # comma-separated to be easily portable into spreadsheet software
        print(SCENARIOS[i], end=", ")
        try:
            print(TIMEFRAMES[j][0], end=", ")
        except Exception as e:
            print(e, end=", ")
        try:
            print(max(customer_SUs), end=", ")
        except Exception as e:
            print(e, end=", ")
        try:
            print(max(attacker_SUs), end=", ")
        except Exception as e:
            print(e, end=", ")
        try:
            print(int(statistics.median(customer_SUs)), end=", ")
        except Exception as e:
            print(e, end=", ")
        try:
            print(int(statistics.median(attacker_SUs)), end=", ")
        except Exception as e:
            print(e, end=", ")
        print("")
