import random
import time
from kubernetes import config, dynamic
from kubernetes.client import api_client, V1PodList


client = dynamic.DynamicClient(
        api_client.ApiClient(configuration=config.load_kube_config())
    )

# define the API resource for Pods
pod_resource = client.resources.get(api_version='v1', kind='Pod')
# list Pods in the "default" namespace
pods: V1PodList = pod_resource.get(namespace='default')
for pod in pods.items:
    print(f"Name: {pod.metadata.name}, Namespace: {pod.metadata.namespace}")

# create coinflip CRD using dynamic client
crd = {
    'apiVersion': 'apiextensions.k8s.io/v1',
    'kind': 'CustomResourceDefinition',
    'metadata': {
        'name': 'coinflipmetrics.test.scale'
    },
    'spec': {
        'group': 'test.scale',
        'names': {
            'kind': 'CoinFlipMetric',
            'plural': 'coinflipmetrics',
            'singular': 'coinflipmetric',
            'shortNames': [
                "cfm"
            ]
        },
        'scope': 'Namespaced',
        'versions': [
            {
                'name': 'v1',
                'served': True,
                'storage': True,
                'schema': {
                    'openAPIV3Schema': {
                        'type': 'object',
                        'properties': {
                            'spec': {
                                'type': 'object',
                                'properties': {
                                    'message': {
                                        'type': 'string'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ],
    },
    'status': {
        'storedVersions': ['v1']
    }
}
try:
    crd_resource = client.resources.get(api_version='apiextensions.k8s.io/v1', kind='CustomResourceDefinition')
    created_crd = crd_resource.create(body=crd)
    print(f"Created CRD {created_crd.metadata.name}")
except:
    pass

# define custom resource
crd_spec = {
    'apiVersion': 'coinflipmetrics.test.scale/v1',
    'kind': 'CoinFlipMetric',
    'metadata': {
        'name': 'test-res',
        'namespace': 'default'
    },
    'spec': {
        'message': 'Hello, Kubernetes!'
    }
}
# create custom resource using dynamic client
my_resource = client.resources.get(api_version='coinflipmetrics.test.scale/v1', kind='CoinFlipMetric')
created_resource = my_resource.create(body=crd_spec, namespace='default')
print(f"Created resource mycrd")

# controller loop
while True:
    # Generate a random coin flip (0 or 1)
    coin_flip = random.randint(0, 1)

    # Wait for 30 seconds before the next update
    time.sleep(30)