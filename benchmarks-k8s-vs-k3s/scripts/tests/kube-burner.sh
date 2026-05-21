#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-}"
INDEXING="${2:-}"

usage() {
  echo "Usage: $0 [dev|prod] [es|local]"
  echo
  echo "  ENVIRONMENT: Define cluster topology 'single-node' or 'highly-available'"
  echo "  INDEXING TYPE: Define indexing type 'elasticsearch' or 'local'."
  exit 1
}

detect_cluster_type() {
  # Get the kubelet version from the first node
  local version
  version=$(kubectl get nodes -o jsonpath='{.items[0].status.nodeInfo.kubeletVersion}' 2>/dev/null)

  if [[ -z "$version" ]]; then
    echo "Error: Could not connect to cluster or no nodes found." >&2
    return 1
  fi

  # Check if the string contains "k3s"
  if [[ "$version" == *"k3s"* ]]; then
    echo "k3s"
  else
    echo "k8s"
  fi
}

CLUSTER_TYPE=$(detect_cluster_type)
echo "Detected cluster type : $CLUSTER_TYPE"

CURRENT_DIRECTORY=$(pwd)

KUBE_BURNER_NS="kube-burner"
KUBE_BURNER_MANIFESTS=../../config/k8s/kube-burner

echo "Configuring Kubernetes API Server FlowSchema and PriorityLevelConfiguration for 'monitoring' Namespace 🏗️"
kubectl apply -f "$CURRENT_DIRECTORY"/../../cluster/flow-schema.yaml
kubectl apply -f "$CURRENT_DIRECTORY"/../../cluster/priority-level-configuration.yaml

echo "Installing Kube Prometheus Stack and VictoriaMetrics 📊🏗️"
kubectl create ns monitoring --dry-run=client -o yaml | kubectl apply -f -

helm repo add --force-update prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add --force-update vm https://victoriametrics.github.io/helm-charts/
helm repo update

echo "Helm repository update completed! ✅"

helm upgrade --install vm-single vm/victoria-metrics-single \
  --namespace monitoring \
  --create-namespace \
  --wait

echo "VictoriaMetrics setup completed! ✅"

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --version ^81.0.0 \
  --namespace monitoring \
  -f ${KUBE_BURNER_MANIFESTS}/../prometheus/additional-datasource-vm.yaml \
  --wait

echo "Prometheus setup completed! ✅"

echo
echo "Deploying Persistent Volume Claim (PVC) for kube-burner 🫙"
kubectl apply -f "${KUBE_BURNER_MANIFESTS}"/namespace.yaml
kubectl apply -f "${KUBE_BURNER_MANIFESTS}/pvc.yaml"


echo "Deploying kube-burner within the cluster 🏗️"
kubectl create configmap kube-burner-manifests \
  --namespace "${KUBE_BURNER_NS}" \
  --from-file "${KUBE_BURNER_MANIFESTS}"/../apps/deployment.yaml \
  --dry-run=client -o yaml | kubectl apply --validate=false -f -

kubectl create configmap kube-burner-config \
  --namespace "${KUBE_BURNER_NS}" \
  --from-file "${KUBE_BURNER_MANIFESTS}"/kube-burner.yaml \
  --from-file "${KUBE_BURNER_MANIFESTS}"/../prometheus/metrics.yaml \
  --from-file "${KUBE_BURNER_MANIFESTS}"/../prometheus/alerts.yaml \
  --dry-run=client -o yaml | kubectl apply --validate=false -f -

kubectl apply -f "${KUBE_BURNER_MANIFESTS}"/job.yaml

echo
echo "Waiting for kube-burner job to complete...⏳"
if kubectl -n "${KUBE_BURNER_NS}" wait \
  --for=condition=complete job/kube-burner-job \
  --timeout=300s; then
  echo "Kube-burner job completed successfully ✅"
else
  echo "WARNING: kube-burner job did NOT complete within timeout ⚠️"
  echo "Continuing script anyway..."
fi

echo
echo "Retrieving kube-burner locally indexed metrics 📫"
kubectl -n "${KUBE_BURNER_NS}" apply -f "${KUBE_BURNER_MANIFESTS}"/metrics-retrieve.yaml
kubectl -n "${KUBE_BURNER_NS}" wait --for=condition=ready pod/kb-metrics-retrieve
kubectl -n "${KUBE_BURNER_NS}" cp kube-burner/kb-metrics-retrieve:/kube-burner/benchmarks ../../benchmarks/${CLUSTER_TYPE}/kube-burner

echo
echo "Cleaning up kube-burner jobs & configs ♻️"
kubectl -n "${KUBE_BURNER_NS}" delete job kube-burner-job --ignore-not-found
kubectl -n "${KUBE_BURNER_NS}" delete pod kb-metrics-retrieve --force --grace-period=0

echo "Cleaning up kube-burner PVC ♻️"
kubectl -n "${KUBE_BURNER_NS}" delete pvc kube-burner-metrics-pvc
echo
echo "Done! ✅"

echo "Next step:"
echo -e "\t1. Change directory to 'benchmarks' on the root directory and execute 'push_metrics_prometheus_push_gateway.sh'"
echo -e "\t2. Build and run Remote Write with VictoriaMetrics in Golang under 'utils'"
