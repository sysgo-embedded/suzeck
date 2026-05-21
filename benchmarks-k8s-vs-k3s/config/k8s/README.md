## Kube-burner usage
Kube-burner is flexible and can be used both ways, but the choice between **CLI (Remote)** and **In-Cluster (Job)** depends entirely on whether we are doing manual "one-off" testing or automated performance regression.

For most performance engineers, running Kube-burner as a binary on a remote computer is the standard approach. When moving toward Production-grade benchmarking or CI/CD pipelines, deploying Kube-burner as a Pod or using the Benchmark Operator is the superior method.

## Kube-burner in-cluster deployment
It works by running Kube-burner as a Job or Pod using its official container image. It uses a service account with the necessary permissions. This method brings the following advantages:
- **CI/CD Pipelines**: Automatically triggering performance tests on every cluster upgrade or configuration change.
- **Network Consistency**: If local computer has a slow or jittery internet connection, "Pod Latency" metrics might be skewed by the time it takes CLI to talk to the API server. Running in-cluster eliminates this "client-side" latency.
- **Long-running tests**: If you are running a "churn" test for 24 hours, you don't want your laptop to go to sleep and kill the process.

## benchmark-operator
**Prometheus** and **Elasticsearch** play different but complementary roles. While Prometheus is used to **collect time-series metrics from the cluster while the benchmark is running**, Elasticsearch is used for **persisting benchmark results and metrics for later analysis and comparison**.

See example usage of benchmark-operator: https://hackmd.io/@rook/SkSMXZ7Jc

> `.spec.system_metrics.es_url` vs `.spec.elasticsearch.url`:
> The first stores **collected system metrics**, while the latter stores **benchmark results and metadata**