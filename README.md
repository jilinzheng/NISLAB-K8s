# Kubernetes (K8s) Economic-Denial-of-Sustainability (EDoS) Local Test Environment

This repo contains resources to set up a local K8s environment to run and collect metrics on EDoS attacks. We utilize Docker Desktop's bundled K8s and deploy Prometheus, Grafana, and Istio as part of its monitoring stack. We use [TeaStore](https://github.com/DescartesResearch/TeaStore) for the target microservice application and JMeter for load generation. Additional notes are included after the installation instructions.

## Installation Instructions

0. Ensure Docker Desktop is installed, has Kubernetes enabled (and running), and Helm is installed.
1. Clone this repository and `cd` into it:

   ```bash
   git clone git@github.com:jilinzheng/NISLAB-K8s.git
   cd NISLAB-K8s
   ```

2. To install Teastore, run the following commands:

   ```bash
   cd teastore
   kubectl apply -f teastore-clusterip.yaml  # TeaStore cluster
   kubectl apply -f teastore-hpa.yaml        # TeaStore Horizontal Pod Autoscaler;
                                             # for randomization tests,
                                             # use teastore-hpa-coinflip.yaml instead
   cd ..    # return to upper directory for next steps
   ```

3. To install the base monitoring stack (Prometheus, node-exporter, kube-state-metrics, metrics-server, Grafana), run the following commands:

   ```bash
   cd monitoring-stack                    # assuming you were in root directory of repo
   kubectl create ns monitoring           # create 'monitoring' namespace
   kubectl apply -f prometheus            # deploy prometheus NOTE: remove pv stuff
   kubectl apply -f node-exporter         # deploy node-exporter
   kubectl apply -f kube-state-metrics    # deploy kube-state-metrics
   kubectl apply -f metrics-server.yaml   # deploy metrics-server
   kubectl apply -f grafana               # deploy grafana
                                          # sample dashboards can be found in
                                          # grafana-dashboards
   ```

4. For the external metrics (randomization metrics and median service units) and Istio metrics (rate of requests to particular services), run the following commands to install Prometheus Adapter and Istio:

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add istio https://istio-release.storage.googleapis.com/charts
   helm repo update
   helm install prometheus-adapter -f prometheus-adapter-helm-chart-values.yaml prometheus-community/prometheus-adapter
   helm install istio-base istio/base -n istio-system --set defaultRevision=default --create-namespace
   helm install istiod istio/istiod -n istio-system --wait
   ```

5. Finish setting up the external and Istio metrics by running the following commands to deploy the external metrics server (Flask API) and enable sidecar injection on the default namespace, where Teastore is deployed (the restarts are to apply the sidecar injection by restarting the deployment):

   ```bash
   kubectl apply -f external-metrics   # assumes you are still in
                                       # the monitoring-stack directory
   kubectl label namespace default istio-injection=enabled --overwrite
   kubectl rollout restart deploy teastore-auth
   kubectl rollout restart deploy teastore-db
   kubectl rollout restart deploy teastore-image
   kubectl rollout restart deploy teastore-persistence
   kubectl rollout restart deploy teastore-recommender
   kubectl rollout restart deploy teastore-registry
   kubectl rollout restart deploy teastore-webui
   ```

6. Access the services on these following URLS!
   - Prometheus: http://localhost:30000
   - Grafana: http://localhost:32000/login
   - Teastore: http://localhost:30080

## Running Load Tests with JMeter

It is fine to edit and run load tests in the GUI mode, but as test plans grow, the GUI mode starts to have more performance issues (typically memory). It is recommended to run load tests in the non-GUI mode, as follows:

`jmeter -n -t [test plan(jmx file)] -l [results file] -e -o [path to empty/nonexistent directory for HTML report]`

Example:

`jmeter -n -t`[`bursty-sliding-window-5x.jmx`](./jmeter-load-testing/scripts/bursty-sliding-window-5x.jmx)`-l results.jtl -e -o html_report`

Upon finishing the load test (assuming it is not in an infinite loop or has a specified thread lifetime), JMeter generates a detailed report of the results of the test in the specified directory (in the example above, the directory name is `html_report`). Simply open `index.html` file within the directory to view the report.

To automate a batch of tests, I have written a script, [automate_load_tests.py](./jmeter-load-testing/automate_load_tests.py), to do exactly that. You just have to update the names of the scripts you wish to run, the output directory of each script, and the location of you JMeter installation. I left some sample scripts, output directories, and location of my JMeter install as a reference.

### Existing Tests

I have included the set of the most recent scripts I used for the SIGMETRICS submission [here](./jmeter-load-testing/scripts/).

To run tests with the default HPA policy (scaling off CPU usage) vs. randomized HPA policy (also scaling off CPU usage, but only if a coinflip is successful shall the CPU usage be updated), **modify the Teastore HPA policy**; there is nothing to do with the JMeter test plans.

## Exporting Metrics

After each test/batch of tests, it can also be useful to export Prometheus metrics (as .csv files) for analysis later, instead of solely relying on Grafana. For that I created three scripts (note that there are required packages you must have in [requirements.txt](./metrics-export/requirements.txt)):

- [`time_series_metrics_export.py`](./metrics-export/time_series_metrics_export.py): queries the local Prometheus HTTP API for the following metrics and writes the time-series data out to .csv files
  - service units over time
  - median service units over time
  - rate of total requests over time
  - rate of successful requests over time
  - rate of failed requests over time
- [`generate_time_series_plots.py`](./metrics-export/generate_time_series_plots.py): generates plots of the .csv files created by [`time_series_metrics_export.py`](./metrics-export/time_series_metrics_export.py) and writes the plots out to .png files
- [`tabular_metrics_export.py`](./metrics-export/tabular_metrics_export.py): queries the local Prometheus HTTP API for max/median customer-/attacker-phase service units used and prints the time-series data out as comma-separated values (to be pasted into a spreadsheet software); essentially a snapshot of the time-series data generated by [`time_series_metrics_export.py`](./metrics-export/time_series_metrics_export.py)

For the [`time_series_metrics_export.py`](./metrics-export/time_series_metrics_export.py) and [`tabular_metrics_export.py`](./metrics-export/tabular_metrics_export.py) scripts, you will have to adjust the scenario names and each scenario's corresponding start/end times (in Unix ms, as outputted by the JMeter test results), all of which are constants at the top of each script. I have left the 'bursty-sliding-window' scenarios as a reference in each script.

I have also left a batch of these exported metrics as a reference of what you should see [here](./metrics-export/sample-metrics-export/).

## Modifying TeaStore Configurations

To change the TeaStore deployments' settings (primarily resource requests/limits), I recommend using a text editor to modify the YAML file directly (all deployment/service configurations for TeaStore are stored in [teastore-clusterip.yaml](teastore/teastore-clusterip.yaml)). The resources of deployments are located in `spec.template.spec.containers.resources`. After modifying all of the desired deployments, save the file, and run

`kubectl apply -f teastore-clusterip.yaml`

in the command line (while being in the same directory as the configuration) to apply the new configuration(s) of the deployment(s).

Similarly, to modify the policy of the Horizontal Pod Autoscaler, modify [teastore-hpa.yaml](teastore/teastore-hpa.yaml), save the file, and run

`kubectl apply -f teastore-hpa.yaml`

in the command line.

To apply the randomized scaling HPA policy, run

`kubectl apply -f teastore-hpa-coinflip.yaml`

## Miscellaneous

### Some Notes on Working with the Precise Throughput Timer

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

NOTE: there are more details I can add here in the future...

## References

- [Monitoring Stack Setup/K8s Tutorial](https://devopscube.com/kubernetes-tutorials-beginners/)
- [TeaStore by DescartesResearch](https://github.com/DescartesResearch/TeaStore)
