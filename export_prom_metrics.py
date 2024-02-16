import requests
import json
import pandas as pd


def main():
    '''Query Prometheus HTTP API for specified metrics, and convert the json response into a csv file.'''

    # Get json responses from Prometheus HTTP API
    prom_api = "http://localhost:30000/api/v1/query"
    pod_response = requests.get(prom_api, params={"query": "rate(container_cpu_usage_seconds_total{image='docker.io/library/nginx:latest'}[5m])"}).json()
    cluster_response = requests.get(prom_api, params={"query": "sum (rate (container_cpu_usage_seconds_total{id='/'}[1m])) / sum (machine_cpu_cores) * 100"}).json()

    # Write json data to a json file
    with open("pod_response.json", 'w') as json_file:
        json.dump(pod_response, json_file, indent=4)
    with open("cluster_response.json", 'w') as json_file:
        json.dump(cluster_response, json_file, indent=4)

    # Convert json to csv
    test_pandas_dataframe = pd.read_json("pod_response.json")
    test_pandas_dataframe.to_csv("pod_response_output.csv", index=False)
    test_pandas_dataframe = pd.read_json("cluster_response.json")
    test_pandas_dataframe.to_csv("cluster_response_output.csv", index=False)


if __name__ == "__main__":
    main()
