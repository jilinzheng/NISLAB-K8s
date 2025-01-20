import requests
import pandas as pd
import statistics

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
    # default autoscaling, random seed
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
    # randomized autoscaling, random seed
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
    # default autoscaling, constant seed
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
    # randomized autoscaling, constant seed
    '1737262034972',
    '1737269878790',
    '1737277739784',
    '1737285613941',
    '1737293515218',
    '1737301366698',
    '1737309220356',
    '1737317079906',
    '1737324937902',
    '1737332804784'
] # unix ms
END_TIMES = [
    # default autoscaling, random seed
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
    # randomized autoscaling, random seed
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
    # default autoscaling, constant seed
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
    # randomized autoscaling, constant seed
    '1737269229695',
    '1737277079090',
    '1737284940413',
    '1737292814675',
    '1737300715537',
    '1737308567221',
    '1737316421122',
    '1737324280155',
    '1737332138185',
    '1737340005053'
] # unix ms
TIMEFRAMES = [
    ('1m', 60),
    ('5m', 300),
    ('15m', 900),
    ('30m', 1800),
    ('1h', 3600)
]
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

if (len(START_TIMES) != len(END_TIMES)
    or len(START_TIMES) != len(SCENARIOS)
    or len(SCENARIOS) != len(END_TIMES)):
    raise ValueError("CONSTANTS length mismatch!")

for i in range(len(SCENARIOS)):
    print(f'----------Scenario: {SCENARIOS[i]}----------')
    for j in range(len(TIMEFRAMES)):
        # for k in range(len(QUERIES)):
        params={
            "query": f'{query_service_units_used(TIMEFRAMES[j][0])}',
            "start": f'{float(START_TIMES[i])/1000.0}',
            "end": f'{float(END_TIMES[i])/1000.0}',
            "step":"15s"
        }
        res = requests.get(PROM_QUERY_RANGE_API, params=params).json()

        # extract desired data: service units
        values = res['data']['result'][0]['values']
        timestamps, target_values = [], []
        for value in values:
            timestamps.append(value[0]) # take the raw second value
            target_values.append(value[1])

        # split SUs into customer/attacker phases (1 hour per each phase)
        # only append if value is applicable within the same test
        # e.g., only include results at the 1-hour mark for the 1-hour timeframe,
        # e.g., only 30-minute and after for the 30-minute timeframe
        customer_SUs, attacker_SUs = [], []
        for k in range(len(timestamps)):
            if (float(END_TIMES[i])/1000.0 - timestamps[k] >= ONE_HOUR_IN_S
                and timestamps[k] > float(START_TIMES[i])/1000.0 + TIMEFRAMES[j][1]):
                customer_SUs.append(int(target_values[k]))
            if (float(END_TIMES[i])/1000.0 - timestamps[k] <= ONE_HOUR_IN_S
                and timestamps[k] > float(START_TIMES[i])/1000.0 + ONE_HOUR_IN_S + TIMEFRAMES[j][1]):
                attacker_SUs.append(int(target_values[k]))
        print(f'Timeframe: {TIMEFRAMES[j][0]}')
        try:
            print(f'- Max customer service units = {max(customer_SUs)}')
        except Exception as e:
            print(f'- {e}')
        try:
            print(f'- Max attacker service units = {max(attacker_SUs)}')
        except Exception as e:
            print(f'- {e}')
        try:
            print(f'- Median customer service units = {int(statistics.median(customer_SUs))}')
        except Exception as e:
            print(f'- {e}')
        try:
            print(f'- Median attacker service units = {int(statistics.median(attacker_SUs))}')
        except Exception as e:
            print(f'- {e}')