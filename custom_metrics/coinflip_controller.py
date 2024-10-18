import random
import time
from kubernetes import client, config, watch

def main():
    try:
        config.load_incluster_config()
        print("Running inside the cluster")
    except config.config_exception.ConfigException:
        config.load_kube_config()
        print("Running outside the cluster")

    custom_api = client.CustomObjectsApi()
    
    while True:
        # Generate a random coin flip (0 or 1)
        coin_flip = random.randint(0, 1)
        
        # Update the CoinFlipMetric custom resource
        try:
            custom_api.replace_namespaced_custom_object(
                group="example.com",
                version="v1",
                namespace="default",
                plural="coinflipmetrics",
                name="mycoinflip",
                body={
                    "apiVersion": "example.com/v1",
                    "kind": "CoinFlipMetric",
                    "metadata": {"name": "mycoinflip"},
                    "spec": {"value": coin_flip}
                }
            )
            print(f"Updated CoinFlipMetric: {coin_flip}")
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # If the resource doesn't exist, create it
                custom_api.create_namespaced_custom_object(
                    group="example.com",
                    version="v1",
                    namespace="default",
                    plural="coinflipmetrics",
                    body={
                        "apiVersion": "example.com/v1",
                        "kind": "CoinFlipMetric",
                        "metadata": {"name": "mycoinflip"},
                        "spec": {"value": coin_flip}
                    }
                )
                print(f"Created CoinFlipMetric: {coin_flip}")
            else:
                print(f"Error updating CoinFlipMetric: {e}")
        
        # Wait for 30 seconds before the next update
        time.sleep(30)

if __name__ == "__main__":
    main()
