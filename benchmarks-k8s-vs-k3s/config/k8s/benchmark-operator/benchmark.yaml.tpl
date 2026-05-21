apiVersion: ripsaw.cloudbulldozer.io/v1alpha1
kind: Benchmark
metadata:
  name: ${BENCH_NAME}
  namespace: benchmark-operator
spec:
  metadata:
    collection: true
    targeted: false

  elasticsearch:
    url: http://${ES_USER}:${ES_PASS}@elasticsearch-master.monitoring.svc.cluster.local:9200

  prometheus:
    es_url: http://elasticsearch-master.monitoring.svc.cluster.local:9200
    prom_url: http://prometheus-server.monitoring.svc.cluster.local:80
    prom_token: ${PROMETHEUS_TOKEN}

  system_metrics:
    collection: true
    es_url: http://${ES_USER}:${ES_PASS}@elasticsearch-master.monitoring.svc.cluster.local:9200
    prom_url: http://prometheus-server.monitoring.svc.cluster.local:80

  workload:
    name: kube-burner
    args:
      workload: ${WORKLOAD}
      image: quay.io/cloud-bulldozer/kube-burner:v1.3
      job_iterations: ${JOB_ITERATIONS}
      qps: ${QPS}
      burst: ${BURST}
      ${EXTRA_ARGS}