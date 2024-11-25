from flask import Flask, Response
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

last_scale_response = ""

@app.route('/metrics')
def metrics():
    global last_scale_response

    # simulate a coin flip: 0 or 1
    coinflip_result = random.choices([0, 1], [0.5, 0.5])
    print(f"coinflip_result = {coinflip_result}")

    # if coinflip is 1/heads, return the proper scaling
    if coinflip_result:
        print(f"coinflip_result = {coinflip_result}")
        last_scale_response = ""
        for i, deploy in enumerate(TARGET_DEPLOYS):
            res = requests.get(PROM_QUERY_INSTANT_API,
                               params=avg_cpu_per_pod_in_deploy(deploy)).json()
            last_scale_response += f"{TARGET_DEPLOYS_UNDERSCORE[i]} {res['data']['result'][0]['value'][1]}\n"
        print(last_scale_response)
        return Response(last_scale_response, mimetype="text/plain")

    # if coinflip is 0/tails, return the last response to prevent another scale
    else:
        print(f"coinflip_result = {coinflip_result}")
        return Response(last_scale_response, mimetype="text/plain")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
