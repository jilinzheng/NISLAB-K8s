# NISLAB K8s Autoscaling Research

## Lab Machine Programs & Ports

- Prometheus: http://localhost:30000
- Alertmanager: http://localhost:31000
- Grafana: http://localhost:32000/login
- JMeter: when executing a load test, must port-forward: `kubectl port-forward --address 0.0.0.0 pod/nginx-7854ff8877-qf62s 8080:80`

## References

- [Monitoring Stack Setup/K8s Tutorial](https://devopscube.com/kubernetes-tutorials-beginners/)
- [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/)
- [PromQL Tutorial](https://valyala.medium.com/promql-tutorial-for-beginners-9ab455142085)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Python JSON to CSV](https://blog.enterprisedna.co/python-convert-json-to-csv/)
- [K8s Monitoring Repo](https://github.com/camilb/prometheus-kubernetes)
- [Resource Usage Queries](https://stackoverflow.com/questions/40327062/how-to-calculate-containers-cpu-usage-in-kubernetes-with-prometheus-as-monitori)
- [Flatteing JSON](https://towardsdatascience.com/flattening-json-objects-in-python-f5343c794b10)
- [More Resource Metrics](https://medium.com/cloud-native-daily/monitoring-kubernetes-pods-resource-usage-with-prometheus-and-grafana-c17848febadc)
