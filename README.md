# NISLAB K8s Autoscaling Research

## Local Installation Instructions

0. Clone this repository. For the NISLAB machine, it is already on the C: drive.
1. Ensure Docker Desktop is installed and has Kubernetes enabled (and running), and Helm is installed.
2. For Teastore, navigate to the `teastore` directory and run the following commands:
   - `kubectl apply -f teastore-clusterip.yaml`
   - `kubectl apply -f teastore-hpa.yaml` (use `teastore-hpa-coinflip.yaml` instead for randomization tests)
3. Create a monitoring namespace with `kubectl create ns monitoring`
4. For the base monitoring stack, navigate to the `monitoring-stack` directory and run the following commands:
   - `kubectl apply -f prometheus`
   - `kubectl apply -f node-exporter`
   - `kubectl apply -f kube-state-metrics`
   - `kubectl apply -f metrics-server`
   - `kubectl apply -f grafana`
5. For the external metrics (randomization metrics and median service units) and Istio metrics (rate of requests to particular services), run the following commands to install Prometheus Adapter and Istio:
   - `helm repo add prometheus-community https://prometheus-community.github.io/helm-charts`
   - `helm repo add istio https://istio-release.storage.googleapis.com/charts`
   - `helm repo update`
   - `helm install prometheus-adapter -f prometheus-adapter-helm-chart-values.yaml prometheus-community/prometheus-adapter`
   - `helm install istio-base istio/base -n istio-system --set defaultRevision=default --create-namespace`
   - `helm install istiod istio/istiod -n istio-system --wait`
6. Finish setting up the external and Istio metrics by running the following commands to deploy the external metrics server (coinflip-depoyment) and enable sidecar injection on the default namespace, where Teastore is deployed (the restarts are to apply the sidecar injection by restarting the deployment):
   - `kubectl apply -f external-metrics`
   - `kubectl label namespace default istio-injection=enabled --overwrite`
   - `kubectl rollout restart deploy teastore-auth`
   - `kubectl rollout restart deploy teastore-db`
   - `kubectl rollout restart deploy teastore-image`
   - `kubectl rollout restart deploy teastore-persistence`
   - `kubectl rollout restart deploy teastore-recommender`
   - `kubectl rollout restart deploy teastore-registry`
   - `kubectl rollout restart deploy teastore-webui`
7. Access the services on these following URLS!
   - Prometheus: http://localhost:30000
   - Grafana: http://localhost:32000/login (user: admin, pass: admin)
   - Teastore: http://localhost:30080

## Debugging

### Localhost

If for some reason `localhost` is not working, try `127.0.0.1`. If that does not work either, perhaps the pod/service is down. Try some of the `kubectl` commands below.

### Useful `kubectl` Commands

- `kubectl get namespaces`
- `kubectl get deploy [deployment name]`
- `kubectl get pod [pod name]`
- `kubectl get servcies [service name]`
- `kubectl get hpa [horizontal pod autoscaler name]`

Switching out `get` with `describe` in any of the above commands will provide a more verbose description of the resource, i.e. `kubectl describe deploy`.

Using the combination of flag and argument `-o yaml` at the end of any of the above commands can also display the YAML version of the resource, e.g., `kubectl get deploy teastore-webui -o yaml`.

By default all of these commands will return the requested resources in the `default` namespace, which is where I have deployed Teastore, but you may wish to check other namespaces for other resources, e.g., the `monitoring` stack. To do so, simply add the flag `-n [namespace]` to see a different namespace, or `--all-namespaces` flag to see all namespaces.

Examples:

- `kubectl get deploy -n monitoring`: get all deployments of the monitoring namespace
- `kubectl get pods --all-namespaces`: get pods across all namespaces

Another very useful command is `kubectl rollout restart deployment [deployment name]`; this will gracefully restart the targeted deployment.

### Useful Helm Commands

- `helm list -A`: list all the Helm charts deployed

## Modifying TeaStore Configurations

To change the TeaStore deployments' settings (primarily resource requests/limits), I recommend using a text editor to modify the YAML file directly (all deployment/service configurations for TeaStore are stored in [teastore-clusterip.yaml](teastore/teastore-clusterip.yaml)). The resources of deployments are located in `spec.template.spec.containers.resources`. After modifying all of the desired deployments, save the file, and run

`kubectl apply -f teastore-clusterip.yaml`

in the command line (while being in the same directory as the configuration) to apply the new configuration(s) of the deployment(s).

Similarly, to modify the policy of the Horizontal Pod Autoscaler, modify [teastore-hpa.yaml](teastore/teastore-hpa.yaml), save the file, and run

`kubectl apply -f teastore-hpa.yaml`

in the command line.

To apply the randomized scaling HPA policy, run

`kubectl apply -f teastore-hpa-coinflip.yaml`

## JMeter

### Running Test Plans

It is fine to edit and run load tests in the GUI mode, but as test plans grow, the GUI mode starts to have more performance issues (typically memory). It is recommended to run load tests in the non-GUI mode, as follows:

`jmeter -n -t [test plan(jmx file)] -l [results file] -e -o [path to empty/nonexistent directory for HTML report]`

Example:

`jmeter -n -t`[`teastore_browse.jmx`](teastore/teastore_browse.jmx)`-l results.jtl -e -o html_report`

Upon finishing the load test (assuming it is not in an infinite loop or has a specified thread lifetime), JMeter generates a detailed report of the results of the test in the specified directory (in the example above, the directory name is `html_report`). Simply open `index.html` file within the directory to view the report.

### Working with the Precise Throughput Timer

There are two main parameters to the Precise Throughput Timer, `Target throughput (in samples per "throughput period")` and `Throughput period (seconds)`. The combination of the two determines the actual throughput of the requests sent by each of the threads. To quote the JMeter user manual, "`Test duration (seconds)` does **not** limit test duration. It is just a hint for the timer."

To properly set the duration of test plans while using the Precise Throughput Timer (perhaps even test plans in general), modify the `Duration (seconds)` in the bottom-most Thread lifetime section of the Thread Group (you may have to check the `Specify Thread lifetime` box).

A basic configuration for a load test is as follows:

- Precise Throughput Timer
  - Target throughput: 2500
  - Throughput period: 600
  - Test duration: 600 (not crucial)
- Thread Group
  - Number of Threads: 1000
  - Ramp-Up period: 0 (leave as zero for the Precise Throughput Timer)
  - Loop Count: Forever
  - Duration: 600
  - Startup delay: 0 (also leave as zero for the Precise Throughput Timer)

This configuration will create 1000 users (threads) to execute the test plan under the Thread Group for ten minutes (600 seconds) with Poisson arrivals (achieved with Precise Throughput Timer).

## References

- [Research Journaling](https://docs.google.com/document/d/1r_4zI_Y6mYxTVYM8sbyfFSwYLj-fthx8k7tVWXRuUEE/edit?usp=sharing)
- [Monitoring Stack Setup/K8s Tutorial](https://devopscube.com/kubernetes-tutorials-beginners/)
- [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [PromQL Tutorial](https://valyala.medium.com/promql-tutorial-for-beginners-9ab455142085)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Python JSON to CSV](https://blog.enterprisedna.co/python-convert-json-to-csv/)
- [K8s Monitoring Repo](https://github.com/camilb/prometheus-kubernetes)
- [Resource Usage Queries](https://stackoverflow.com/questions/40327062/how-to-calculate-containers-cpu-usage-in-kubernetes-with-prometheus-as-monitori)
- [Flattening JSON](https://towardsdatascience.com/flattening-json-objects-in-python-f5343c794b10)
- [More Resource Metrics](https://medium.com/cloud-native-daily/monitoring-kubernetes-pods-resource-usage-with-prometheus-and-grafana-c17848febadc)
- [K8s Deployment YAML Examples](https://codefresh.io/learn/kubernetes-deployment/kubernetes-deployment-yaml/)
- [K8s Dev Guide for Beginners](https://www.youtube.com/playlist?list=PLHq1uqvAteVvUEdqaBeMK2awVThNujwMd)
- [Precise Throughput Timer](https://jmeter.apache.org/usermanual/component_reference.html#Precise_Throughput_Timer)
- https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus-adapter
- https://istio.io/latest/docs/setup/install/helm/
- https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/
