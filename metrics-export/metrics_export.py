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
    # 'no_attacker',
    # 'ddos_5x',
    # 'ddos_10x',
    # 'ddos_20x',
    # 'yoyo_5x',
    # 'yoyo_10x',
    # 'yoyo_20x',
    # 'state_aware_5x',
    # 'state_aware_10x',
    # 'state_aware_20x'
    'ddos_20x_default_hpa_random_seed',
    'ddos_20x_default_hpa_constant_seed',
    'ddos_20x_randomized_hpa_random_seed',
    'ddos_20x_randomized_hpa_constant_seed'
]
START_TIMES = [
    # '1736924542155',
    # '1736932434836',
    # '1736940350999',
    # '1736948291583',
    # '1736956288330',
    # '1736964185797',
    # '1736972089479',
    # '1736980004527',
    # '1737084936193',
    # '1737092804278',
    # '1737101140024',
    # '1737108988075',
    # '1737116849058',
    # '1737124723454',
    # '1737132626930',
    # '1737140481553',
    # '1737148391455',
    # '1737156255896',
    # '1737164119432',
    # '1737171990194',
    # '1737181019924',
    # '1737188867253',
    # '1737196733663',
    # '1737204614284',
    # '1737212525869',
    # '1737220381299',
    # '1737228239701',
    # '1737236103688',
    # '1737243961303',
    # '1737251834095',
    # '1737262034972',
    # '1737269878790',
    # '1737277739784',
    # '1737285613941',
    # '1737293515218',
    # '1737301366698',
    # '1737309220356',
    # '1737317079906',
    # '1737324937902',
    # '1737332804784'
    # ddos-20x re-runs
    '1737410733094',
    '1737418636106',
    '1737427121796',
    '1737435021493'
] # unix ms
END_TIMES = [
    # '1736931742413',
    # '1736939635116',
    # '1736947551403',
    # '1736955492130',
    # '1736963488646',
    # '1736971386169',
    # '1736979292620',
    # '1736987204824',
    # '1737092136458',
    # '1737100002170',
    # '1737171990194',
    # '1737116188358',
    # '1737124049370',
    # '1737131923927',
    # '1737139827303',
    # '1737147682058',
    # '1737155592043',
    # '1737163456124',
    # '1737171316976',
    # '1737179190522',
    # '1737188214777',
    # '1737196067535',
    # '1737203934010',
    # '1737211815119',
    # '1737219726227',
    # '1737227581730',
    # '1737235440372',
    # '1737243298499',
    # '1737251161574',
    # '1737259034346',
    # '1737269229695',
    # '1737277079090',
    # '1737284940413',
    # '1737292814675',
    # '1737300715537',
    # '1737308567221',
    # '1737316421122',
    # '1737324280155',
    # '1737332138185',
    # '1737340005053'
    '1737417934508',
    '1737425837273',
    '1737434323134',
    '1737442222831'
] # unix ms
TIMEFRAMES = ['1m','5m','15m','30m','1h']

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
    (query_service_units_used, 'Service Units Used')
    # (query_median_service_units_used, 'Median Service Units Used')
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
            filename = f'./250120_{SCENARIOS[i]}_{QUERIES[k][1].replace(' ','_').lower()}_{TIMEFRAMES[j]}.csv'
            df = pd.DataFrame({
                'Timestamp': timestamps,
                f'{QUERIES[k][1]}': target_values
            })
            # df.to_excel('./prom_res.xlsx', index=False, engine='openpyxl')
            df.to_csv(filename,index=False)
            print(f'{filename} successfully written!')