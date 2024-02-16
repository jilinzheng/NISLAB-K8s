import requests
import json
import pandas as pd


def flatten_json(nested_json, exclude=['']):
    """Flatten json object with nested keys into a single level.
        Args:
            nested_json: A nested json object.
            exclude: Keys to exclude from output.
        Returns:
            The flattened json object if successful, None otherwise.
    """
    out = {}

    def flatten(x, name='', exclude=exclude):
        if type(x) is dict:
            for a in x:
                if a not in exclude: flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out


def main():
    '''Query Prometheus HTTP API for specified metrics, and convert the json response into a csv file.'''
    ''' DON'T EDIT FOR NOW
    # Get json responses from Prometheus HTTP API
    prom_api = "http://localhost:30000/api/v1/query"
    pod_response = requests.get(prom_api, params={"query": "rate(container_cpu_usage_seconds_total{image='docker.io/library/nginx:latest'}[5m])"}).json()
    cluster_response = requests.get(prom_api, params={"query": "sum (rate (container_cpu_usage_seconds_total{id='/'}[1m])) / sum (machine_cpu_cores) * 100"}).json()

    # Write json data to a json file to verify proper response
    with open("pod_response.json", 'w') as json_file:
        json.dump(pod_response, json_file, indent=4)
    with open("cluster_response.json", 'w') as json_file:
        json.dump(cluster_response, json_file, indent=4)
    '''
    # Flatten json
    f = open("pod_response.json")
    pod_json = json.dumps(f)
    breakpoint()
    # Convert json to csv
    #test_pandas_dataframe = pd.read_json("pod_response.json")
    test_pandas_dataframe = flatten_json(pod_json)
    breakpoint()
    test_pandas_dataframe = pd.read_json(test_pandas_dataframe)
    test_pandas_dataframe.to_csv("pod_response_output.csv", index=False)
    #test_pandas_dataframe = pd.read_json("cluster_response.json")
    #test_pandas_dataframe.to_csv("cluster_response_output.csv", index=False)


if __name__ == "__main__":
    main()
