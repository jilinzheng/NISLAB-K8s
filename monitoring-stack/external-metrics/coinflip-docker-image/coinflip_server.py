from flask import Flask, Response
import random
import requests
import time
import statistics

# Prometheus APIs
# PROM_QUERY_INSTANT_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query"
# PROM_QUERY_RANGE_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query_range"
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# list of target deployments
TARGET_DEPLOYS = (['teastore-auth',
                  'teastore-db',
                  'teastore-image',
                  'teastore-persistence',
                  'teastore-recommender',
                  'teastore-registry',
                  'teastore-webui'])
TARGET_DEPLOYS_UNDERSCORE = [deploy.replace('-','_') for deploy in TARGET_DEPLOYS]
TIMEFRAMES = ['1m','5m','10m','15m','20m','30m','45m','1h']
TIMEFRAMES_SECONDS = [60,300,600,900,1200,1800,2700,3600]
MEDIAN_METRIC_NAMES=[f"median_service_units_{timeframe}" for timeframe in TIMEFRAMES]
last_randomization_response = ""

# average cpu utilization per pod of deployment
def avg_cpu_per_pod_in_deploy(deployment):
    return {
        "query":
        f"""sum(rate(container_cpu_usage_seconds_total{{namespace="default",pod=~"{deployment}-.*"}}[1m])) /
            scalar(count(kube_pod_info{{namespace="default",created_by_name=~"{deployment}-.*"}}))"""
    }

def get_randomization_metrics():
    global last_randomization_response

    # simulate a coin flip: 0 or 1
    coinflip = random.choices([0, 1], [0.5, 0.5])

    # if coinflip is 1/heads, clear the last response and return the proper scaling
    if coinflip:
        last_randomization_response = ""
        for i, deploy in enumerate(TARGET_DEPLOYS):
            res = requests.get(PROM_QUERY_INSTANT_API,
                               params=avg_cpu_per_pod_in_deploy(deploy)).json()
            last_randomization_response += f"{TARGET_DEPLOYS_UNDERSCORE[i]} {res['data']['result'][0]['value'][1]}\n"
        return last_randomization_response
    
    # if coinflip is 0/tails, return the last response to prevent another scale
    else:
        return last_randomization_response


def median_service_units(start_time, end_time, timeframe):
    return {
        "query":
        f"""ceil(
            sum(rate(container_cpu_usage_seconds_total{{namespace="default"}}[{timeframe}])) >
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024)) or
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024))
        )""",
        "start":f'{start_time}',
        "end":f'{end_time}',
        "step":f"{timeframe}"
    }

def get_median_metrics():
    median_metrics = ""
    for i, timeframe in enumerate(TIMEFRAMES):
        res = requests.get(PROM_QUERY_RANGE_API,
                        params=median_service_units(time.time()-TIMEFRAMES_SECONDS[i],
                                                    time.time(),
                                                    timeframe)).json()
        res_values = res['data']['result'][0]['values']
        service_units = []
        for value in res_values:
            service_units.append(float(value[1]))
        median_metrics += f"{MEDIAN_METRIC_NAMES[i]} {statistics.median(service_units)}\n"
    return median_metrics

app = Flask(__name__)

@app.route('/')
def index():
    hundred_samples = random.choices([0,1],[0.7,0.3],k=100)
    zeros = 0
    ones = 0
    for sample in hundred_samples:
        if sample:
            ones+=1
        else:
            zeros+=1
    res = f"Coinflip server up and running!\nOut of a hundred samples, zeros = {zeros} and ones = {ones}!"
    return Response(res, mimetype="text/plain")

@app.route('/metrics')
def metrics():
    return Response(get_randomization_metrics()+get_median_metrics(), mimetype="text/plain")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
