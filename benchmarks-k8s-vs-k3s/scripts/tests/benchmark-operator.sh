#!/bin/bash
# set -xeuo pipefail

# ENVIRONMENT="${1:-}"
# BENCH="${2:?cluster|node|pod}"

ENVIRONMENT="${1:-}"
BENCH="${2:-}"
usage() {
  echo "Usage: $0 [dev|prod] [cluster|node|pod]"
  echo
  echo "  ENVIRONMENT  Required. One of dev, prod."
  echo "  BENCH        Required. One of: cluster, node, pod."
  exit 1
}

HELM_ELASTICSEARCH_EXTRA_ARGS=()

case "$ENVIRONMENT" in
  dev)
    HELM_ELASTICSEARCH_EXTRA_ARGS+=(
      --set replicas=1
      --set minimumMasterNodes=1
      # 1. Fix the "Broken Pipe": Disable security/TLS so http:// works
      --set protocol=http
      --set createCert=false
      --set esConfig."elasticsearch\.yml"="xpack.security.enabled: false
xpack.security.http.ssl.enabled: false"
      # 2. Fix the Helm timeout: A 1-node cluster will be 'yellow', never 'green'
      --set clusterHealthCheckParams="wait_for_status=yellow&timeout=1s"
      # --set extraEnvs[0].name="discovery.type"
      # --set extraEnvs[0].value="single-node"
    )
    ;;
  prod|"")
    # no extra args
    ;;
  *)
    echo "❌ Invalid environment: '$ENVIRONMENT'"
    usage
    exit 1
    ;;
esac

case "$BENCH" in
  cluster)
    export BENCH_NAME="cluster-density-test"
    export WORKLOAD="cluster-density"
    export JOB_ITERATIONS=100
    export QPS=20
    export BURST=20
    export EXTRA_ARGS=""
    ;;
  node)
    export BENCH_NAME="node-density-test"
    export WORKLOAD="node-density"
    export JOB_ITERATIONS=110
    export QPS=50
    export BURST=50
    export EXTRA_ARGS=""
    ;;
  pod)
    export BENCH_NAME="pod-density-test"
    export WORKLOAD="pod-density"
    export JOB_ITERATIONS=20
    export QPS=2
    export BURST=2
    export EXTRA_ARGS=""
    ;;
  *)
    echo "❌ Invalid benchmarking test: '$BENCH'"
    usage
    exit 1
    ;;
esac

OUT_DIR="../../results"
mkdir -p "${OUT_DIR}"

echo "I. Deploy benchmark-operator in cluster"
git clone https://github.com/cloud-bulldozer/benchmark-operator
cd benchmark-operator/charts/benchmark-operator
helm upgrade --wait --install benchmark-operator . -n benchmark-operator --create-namespace
cd ../../.. && rm -rf benchmark-operator

echo "II. Install Prometheus and ElasticSearch"
kubectl create ns monitoring --dry-run=client -o yaml | kubectl apply -f -

helm repo add --force-update prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add --force-update elastic https://helm.elastic.co
helm repo update


helm upgrade --install prometheus prometheus-community/prometheus \
  --namespace monitoring \
  --wait

echo "Prometheus setup completed!"
echo

helm upgrade --install elasticsearch elastic/elasticsearch \
  --namespace monitoring \
  --wait \
  "${HELM_ELASTICSEARCH_EXTRA_ARGS[@]}"

echo "Elasticsearch setup completed"
echo  

echo "III. Patching benchmark-operator manifests"

# kubectl create configmap kube-burner-prom \
#   --namespace benchmark-operator \
#   --from-file=../../config/k8s/prometheus/metrics.yaml \
#   --from-file=../../config/k8s/prometheus/alerts.yaml \
#   --dry-run=client -o yaml | kubectl apply --validate=false -f -

export ES_USER=$(kubectl -n monitoring get secret elasticsearch-master-credentials \
  -o jsonpath='{.data.username}' | base64 -d)
export ES_PASS=$(kubectl -n monitoring get secret elasticsearch-master-credentials \
  -o jsonpath='{.data.password}' | base64 -d)

export PROMETHEUS_TOKEN=$(kubectl -n=monitoring create token prometheus-server)

envsubst < ../../config/k8s/benchmark-operator/benchmark.yaml.tpl > ../../config/k8s/benchmark-operator/${BENCH}-density.test.yaml

kubectl apply -f ../../config/k8s/benchmark-operator/${BENCH}-density.test.yaml
## ==================================================
## NOT NEEDED! Use the in-cluster DNS cluster instead
# echo "III. a) Capture the endpointslices address for Prometheus and ElasticSearch"
# kubectl get endpointslice \
#   --namespace monitoring

# IP[0] is for Prometheus Endpoint, IP[1] is for Elasticsearch Endpoint
# IPS=$(kubectl get endpointslice -n monitoring -o json \
#   | jq -r '
#     .items[]
#     | select(.metadata.labels["kubernetes.io/service-name"]=="prometheus-server"
#           or .metadata.labels["kubernetes.io/service-name"]=="elasticsearch-master")
#     | .endpoints[].addresses[]
#   ' \
#   | sort -u \
#   | paste -sd "," -
# )
## ==================================================
