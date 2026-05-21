# Kube-Burner Metrics Remote Write Scripts
Push kube-burner metrics to VictoriaMetrics primarly with **preserved timestamps**. Pushing to Prometheus is also possible but requires additional steps and it will result in losing the original timestamps by design.

The implementation is in Golang for scale and performance goals with the use of `protobuf` and `snappy` compression 
## Quick Start - VictoriaMetrics (Recommended)
VictoriaMetrics has the simplest import API:

### Installation
Golang is able to compile a cross-compile and a statically linked binary through the variable that we pass to the compiler  
* GOOS: Input the operating system. Possible values are: <"linux"-"windows">
* GOARCH: Input the CPU architecture. Possible values are: <"amd64"-"arm64">
* CGO_ENABLED:

  * CGO_ENABLED=1
    Go compiler allows the use of the import "C" pseudo-package. This is essential when your Go code needs to talk to:
    * Standard C libraries (like libc)
    * Graphics libraries (OpenGL, SDL).
    * Database drivers that wrap C engines (like the popular sqlite3 driver).

    Trade-offs
    * Slower Builds: You aren't just compiling Go; you're invoking a C compiler too.
    * Binary Portability: The resulting binary is usually **dynamically linked**. This means it might depend on specific versions of libraries (like glibc) being present on the target machine.
    * Complexity: Debugging becomes harder as tools like delve have to navigate the boundary between Go's stack and C's stack.

  * CGO_ENABLED=0
    Go compiler to use **pure Go** implementations of everything.

    Benefits:
    * Static Binaries: This is the "Go Holy Grail." It produces a single, completely self-contained file. You can drop this binary into a scratch Docker image or a different Linux distro, and it will just work because it has zero external dependencies.
    * Faster Compilation: The overhead of the C toolchain is removed.
    * Cross-Compilation: It makes building for different OSs (e.g., building a Linux binary on a Mac) much simpler because you don't need a cross-platform C compiler.

```bash
CGO_ENABLED=0 GOOS=<operating-system> GOARCH=<cpu-arch> go build -o build/push-json-metrics-prometheus-<operating-system>-<cpu-arch>
```

### Usage
The binary can be executed from every directory since it relies on absolute paths. We pass the following flags:
* `--remote-write`: Possible values: `victoria-metrics` or `prometheus`
* `--service-name`: This might change depending on the `--remote-write` url chosen or the helm chart of victoria-metrics! for the single server mode the service-name is the following `vm-single-victoria-metrics-single-server`
```bash
./build/push-json-metrics-prometheus-linux-amd64 --remote-write=<remote-write> --service-name=<service-name>
```

## Prometheus Setup (if using Prometheus instead of VictoriaMetrics)
Add to your `prometheus.yml`:

```yaml
# Enable remote write receiver (Prometheus 2.33+)
remote_write_receiver:
  enabled: true
```

## Query Your Data
Once imported, you can query in Prometheus/Grafana:

```promql
# Compare K3s vs K8s CPU usage
node_cpu_seconds{instance="k3s"}
node_cpu_seconds{instance="k8s"}

# Compare by mode
node_cpu_seconds{mode="user", instance="k3s"}
node_cpu_seconds{mode="user", instance="k8s"}
```

## Timestamps
✅ **Original timestamps are preserved with VictoriaMetrics!** 

The scripts convert the ISO 8601 timestamps from your JSON files to Unix milliseconds and send them with the metrics.

Example:
- JSON: `"timestamp":"2026-02-06T22:41:38.293Z"`
- Sent as: `1738881698293` (milliseconds since epoch)

## Troubleshooting
### Go: Module errors
```bash
go mod tidy
go build
```

### Connection refused
Make sure VictoriaMetrics/Prometheus is running:
```bash
# VictoriaMetrics
curl http://localhost:8428/metrics

# Prometheus
curl http://localhost:9090/api/v1/status/config
```

### "remote write receiver is not enabled"
Add to prometheus.yml:
```yaml
remote_write_receiver:
  enabled: true
```