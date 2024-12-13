from flask import Flask, Response
import requests
import time
import statistics

# Prometheus APIs
# PROM_QUERY_INSTANT_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query"
# PROM_QUERY_RANGE_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query_range"
PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

TIMEFRAMES = ['1m','5m','10m','15m','20m','30m','45m','1h']
TIMEFRAMES_SECONDS = [60,300,600,900,1200,1800,2700,3600]
METRIC_NAMES=[f"service_units_{timeframe}" for timeframe in TIMEFRAMES]
TARGET_SERVICE_UNITS = 8

def query_service_units(start_time, end_time, timeframe):
    return {
        "query":
        f"""ceil(
            sum(rate(container_cpu_usage_seconds_total{{namespace="default"}}[{timeframe}])) >
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024)) or
            sum(container_memory_working_set_bytes{{namespace='default'}} / (4 * 1024 * 1024 * 1024))
        )""",
        "start":f'{start_time}',
        "end":f'{end_time}',
        "step":f"1m"
    }

def get_service_unit_metrics():
    metrics = ""
    for i, timeframe in enumerate(TIMEFRAMES):
        res = requests.get(PROM_QUERY_RANGE_API,
                        params=query_service_units(time.time()-3600,    # query results from
                                                    time.time(),        # one hour ago til now
                                                    timeframe)).json()
        print(time.time())
        print(res)
        res_values = res['data']['result'][0]['values']
        latest_service_unit_count = res_values[-1][1]
        metrics += f"{METRIC_NAMES[i]} {latest_service_unit_count}\n"
    return metrics

app = Flask(__name__)

@app.route('/')
def index():
    return Response(get_service_unit_metrics(), mimetype="text/plain")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
