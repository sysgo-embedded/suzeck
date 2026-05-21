#!/bin/bash
set -euo pipefail

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

# Files expected next to this script:
IPERF3_SERVER_MANIFESTS=../../config/network/iperf3-server.yaml
IPERF3_CLIENT_MANIFESTS=../../config/network/iperf3-client.yaml

OUT_DIR=../../benchmarks/"$CLUSTER_TYPE"/iperf3

mkdir -p "${OUT_DIR}"

echo
echo "=== 1) Deploy iperf3 server + service ==="
kubectl apply -f "${IPERF3_SERVER_MANIFESTS}"

echo "Waiting for iperf3 server rollout..."
# assumes deployment name is iperf3-server (matching your manifest)
kubectl rollout status deployment/iperf3-server --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=iperf3-server --timeout=120s || true

echo
echo "=== 2) Run iperf3 client job ==="
# assumes the client Job is named iperf3-client in the manifest
kubectl apply -f "${IPERF3_CLIENT_MANIFESTS}"  # safe to re-apply if iperf manifest contains both server+client
echo "Waiting for job/iperf3-client to complete..."
kubectl wait --for=condition=complete job/iperf3-client --timeout=180s
echo "Collecting iperf3 logs..."
kubectl logs job/iperf3-client > "${OUT_DIR}/iperf3.log"
echo "iperf3 log saved to ${OUT_DIR}/iperf3.log"

echo
echo "=== 3) Clean-up iperf3-server and iperf3-client workloads ==="
kubectl delete -f "${IPERF3_CLIENT_MANIFESTS}" 
kubectl delete -f "${IPERF3_SERVER_MANIFESTS}"