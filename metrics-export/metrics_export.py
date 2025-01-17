"""
Query Prometheus HTTP API for specified metrics
"""

import requests
from datetime import datetime
import pandas as pd

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

SCENARIOS = [
    'no_attacker',
    'ddos_5x',
    'ddos_10x',
    'ddos_20x',
    'yoyo_5x',
    'yoyo_10x',
    'yoyo_20x',
    'state_aware_5x',
    'state_aware_10x',
    'state_aware_20x'
]
START_TIMES = [
    '1736924542155',
    '1736932434836',
    '1736940350999',
    '1736948291583',
    '1736956288330',
    '1736964185797',
    '1736972089479',
    '1736980004527',
    '1736987928584',
    '1736995799604'
] # unix ms
END_TIMES = [
    '1736931742413',
    '1736939635116',
    '1736947551403',
    '1736955492130',
    '1736963488646',
    '1736971386169',
    '1736979292620',
    '1736987204824',
    '1736995128875',
    '1737003000015'
] # unix ms
TIMEFRAMES = ['1m','5m','10m','15m','20m','30m','45m','1h']

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
    (query_rate_of_total_requests, 'Rate of Total Requests'),
    (query_rate_of_successful_requests, 'Rate of Successful Requests'),
    (query_rate_of_failed_requests, 'Rate of Failed Requests'),
    (query_service_units_used, 'Service Units Used'),
    (query_median_service_units_used, 'Median Service Units Used')
]

if (len(START_TIMES) != len(END_TIMES)
    or len(START_TIMES) != len(SCENARIOS)
    or len(SCENARIOS) != len(END_TIMES)):
    raise ValueError("CONSTANTS length mismatch!")

for i in range(len(SCENARIOS)):
    for j in range(len(TIMEFRAMES)):
        for k in range(len(QUERIES)):
            params={
                "query": f'{QUERIES[k][0](TIMEFRAMES[j])}',
                "start": f'{float(START_TIMES[i])/1000.0}',
                "end": f'{float(END_TIMES[i])/1000.0}',
                "step":"15s"
            }
            res = requests.get(PROM_QUERY_RANGE_API, params=params).json()

            # extract desired data
            values = res['data']['result'][0]['values']
            timestamps, target_values = [], []
            for value in values:
                timestamp = value[0]
                timestamps.append(datetime.fromtimestamp(timestamp))
                target_values.append(value[1])

            # create dataframe + write to csv
            filename = f'./250116_{SCENARIOS[i]}_{QUERIES[k][1].replace(' ','_').lower()}_{TIMEFRAMES[j]}.csv'
            df = pd.DataFrame({
                'Timestamp': timestamps,
                f'{QUERIES[k][1]}': target_values
            })
            # df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
            df.to_csv(filename,index=False)
            print(f'{filename} successfully written!')