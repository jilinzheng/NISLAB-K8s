from flask import Flask
import random
import requests

# Prometheus APIs
PROM_QUERY_INSTANT_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query"
PROM_QUERY_RANGE_API = "http://prometheus-service.monitoring.svc.cluster.local:9090/api/v1/query_range"
# PROM_QUERY_INSTANT_API = "http://127.0.0.1:30000/api/v1/query"
# PROM_QUERY_RANGE_API = "http://127.0.0.1:30000/api/v1/query_range"

# list of target deployments
TARGET_DEPLOYS = (['teastore-auth',
                  'teastore-db',
                  'teastore-image',
                  'teastore-persistence',
                  'teastore-recommender',
                  'teastore-registry',
                  'teastore-webui'])

TARGET_DEPLOYS_UNDERSCORE = [deploy.replace('-','_') for deploy in TARGET_DEPLOYS]

# average cpu utilization per pod of deployment
def avg_cpu_per_pod_in_deploy(deployment):
    return {"query":
            f"""sum(
                    rate(container_cpu_usage_seconds_total{{
                        namespace="default",
                        pod=~"{deployment}-.*"}}
                        [1m]
                        ))
                /
                scalar(
                    count(
                        kube_pod_info{{
                            namespace="default",
                            created_by_name=~"{deployment}-.*"
                            }}))
            """}

app = Flask(__name__)

@app.route('/')
def index():
    return "Coinflip server up and running!"

last_scale_response = ""

@app.route('/metrics')
def metrics():
    global last_scale_response

    # simulate a coin flip: 0 or 1
    coinflip_result = random.choice([0, 1])

    # if coinflip is 1/heads, return the proper scaling
    if coinflip_result:
        print(f"coinflip_result = {coinflip_result}")
        last_scale_response = ""
        for i, deploy in enumerate(TARGET_DEPLOYS):
            res = requests.get(PROM_QUERY_INSTANT_API,
                               params=avg_cpu_per_pod_in_deploy(deploy)).json()
            last_scale_response += f"{TARGET_DEPLOYS_UNDERSCORE[i]} {res['data']['result'][0]['value'][1]}\n"
        print(last_scale_response)
        return last_scale_response

    # if coinflip is 0/tails, return the last response to prevent another scale
    else:
        print(f"coinflip_result = {coinflip_result}")
        return last_scale_response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
