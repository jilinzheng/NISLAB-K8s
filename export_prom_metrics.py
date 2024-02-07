import requests
import json
import pandas as pd


def main():
    '''Query Prometheus HTTP API for specified metrics, and convert the json response into a csv file.'''

    # Get json response from HTTP API
    prom_api = "http://localhost:30000/api/v1/query"
    test_response = requests.get(prom_api, params={"query": "container_cpu_user_seconds_total"})
    data = test_response.json()
    
    # Write json data to a json file
    with open("test_json.json", 'w') as json_file:
        json.dump(data, json_file)
    #test_json = json.load(test_response)
    #print(type(test_json))

    # Convert json to csv
    
    test_pandas_dataframe = pd.read_json("test_json.json")
    print(test_pandas_dataframe)
    test_pandas_dataframe.to_csv("output.csv", index=False)
    


if __name__ == "__main__":
    main()
