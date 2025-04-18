import random
import requests
import time
import statistics
from flask import Flask, Response


# Prometheus APIs
PROM_QUERY_INSTANT_API = (
    "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query"
)
PROM_QUERY_RANGE_API = (
    "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query_range"
)
# PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
# PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# list of target deployments
TARGET_DEPLOYS = [
    "teastore-auth",
    "teastore-db",
    "teastore-image",
    "teastore-persistence",
    "teastore-recommender",
    "teastore-registry",
    "teastore-webui",
]
TARGET_DEPLOYS_UNDERSCORE = [deploy.replace("-", "_") for deploy in TARGET_DEPLOYS]
TIMEFRAMES = ["1m", "5m", "10m", "20m", "30m", "1h"]
TIMEFRAMES_SECONDS = [60, 300, 600, 1200, 1800, 3600]


# average cpu utilization per pod of deployment
def query_avg_cpu_per_pod_in_deploy(deployment):
    return {
        "query": f"""sum(rate(container_cpu_usage_seconds_total{{namespace="default",pod=~"{deployment}-.*"}}[1m])) /
            scalar(count(kube_pod_info{{namespace="default",created_by_name=~"{deployment}-.*"}}))"""
    }


def query_service_units(start_time, end_time, timeframe):
    return {
        "query": f"""ceil(
            sum(rate(container_cpu_usage_seconds_total{{namespace="default"}}[{timeframe}])) >
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024)) or
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024))
        )""",
        "start": f"{start_time}",
        "end": f"{end_time}",
        "step": f"{timeframe}",
    }


last_randomization_response = ""


def get_randomization_metrics():
    global last_randomization_response

    # simulate a coin flip: 0 or 1
    coinflip = random.choices([0, 1], [0.5, 0.5])

    # if coinflip is 1/heads, clear the last response and return the proper scaling
    if coinflip:
        last_randomization_response = ""
        for i, deploy in enumerate(TARGET_DEPLOYS):
            res = requests.get(
                PROM_QUERY_INSTANT_API, params=query_avg_cpu_per_pod_in_deploy(deploy)
            ).json()
            last_randomization_response += f"{TARGET_DEPLOYS_UNDERSCORE[i]} {res['data']['result'][0]['value'][1]}\n"
        return last_randomization_response

    # if coinflip is 0/tails, return the last response to prevent another scale
    else:
        return last_randomization_response


def get_median_metrics():
    MEDIAN_METRIC_NAMES = [
        f"median_service_units_{timeframe}" for timeframe in TIMEFRAMES
    ]
    median_metrics = ""
    for i, timeframe in enumerate(TIMEFRAMES):
        res = requests.get(
            PROM_QUERY_RANGE_API,
            params=query_service_units(
                # query results from two hours ago til now
                time.time() - 7200,
                time.time(),
                timeframe,
            ),
        ).json()
        res_values = res["data"]["result"][0]["values"]
        service_units = []
        for value in res_values:
            service_units.append(int(value[1]))
        median_metrics += (
            f"{MEDIAN_METRIC_NAMES[i]} {statistics.median(service_units)}\n"
        )
    return median_metrics


last_service_unit_amount = -1


def get_state_aware_attack():
    global last_service_unit_amount
    STATE_AWARE_ATTACK_THRESHOLD = 10

    res = requests.get(
        PROM_QUERY_RANGE_API,
        params=query_service_units(
            # query results from 1 minute ago til now
            time.time() - 60,
            time.time(),
            "1m",
        ),
    ).json()
    res_values = res["data"]["result"][0]["values"]
    new_service_unit_amount = int(res_values[0][1])

    # decrease detected + original number of SUs > threshold
    if (
        last_service_unit_amount > new_service_unit_amount
        and last_service_unit_amount > STATE_AWARE_ATTACK_THRESHOLD
    ):
        last_service_unit_amount = new_service_unit_amount
        # attacker should inject traffic burst
        return "state_aware_attack 1\n"

    last_service_unit_amount = new_service_unit_amount
    # attacker should NOT inject traffic burst
    return "state_aware_attack 0\n"


time_since_last_attack = time.time()


def get_sliding_window_attack():
    global time_since_last_attack
    SLIDING_WINDOW_ATTACK_THRESHOLD_SU = 10
    res = requests.get(
        PROM_QUERY_RANGE_API,
        params=query_service_units(
            # query results from 5 minutes ago til now
            time.time() - 300,
            time.time(),
            "5m",
        ),
    ).json()
    res_values = res["data"]["result"][0]["values"]
    five_min_rolling_avg_service_units = int(res_values[0][1])

    # >=5 minutes elapsed and below or equal to attack threshold
    if (
        time.time() - time_since_last_attack >= 300
        and five_min_rolling_avg_service_units <= SLIDING_WINDOW_ATTACK_THRESHOLD_SU
    ):
        # reset last attack time
        time_since_last_attack = time.time()
        # attacker should inject traffic burst
        print("Attacker injecting traffic!")
        return "sliding_window_attack 1\n"

    # attacker should NOT inject traffic burst
    return "sliding_window_attack 0\n"


app = Flask(__name__)


@app.route("/")
def index():
    hundred_samples = random.choices([0, 1], [0.7, 0.3], k=100)
    zeros = 0
    ones = 0
    for sample in hundred_samples:
        if sample:
            ones += 1
        else:
            zeros += 1
    res = f"Coinflip server up and running!\nOut of a hundred samples, zeros = {zeros} and ones = {ones}!\n"
    return Response(res, mimetype="text/plain")


@app.route("/metrics")
def metrics():
    return Response(
        get_randomization_metrics()
        + get_median_metrics()
        + get_state_aware_attack()
        + get_sliding_window_attack(),
        mimetype="text/plain",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
