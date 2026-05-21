#!/bin/bash
set -euo pipefail

# Files expected next to this script:
SYSBENCH_MANIFESTS=../../config/host/

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

OUT_DIR=../../benchmarks/"$CLUSTER_TYPE"/sysbench

mkdir -p "${OUT_DIR}"


echo
echo "=== Run sysbench CPU & memory jobs ==="
kubectl apply -f "${SYSBENCH_MANIFESTS}"
for job in sysbench-cpu sysbench-mem; do
  echo "Waiting for job/${job} to complete..."
  kubectl wait --for=condition=complete "job/${job}" --timeout=180s
  echo "Collecting logs for ${job}..."
  kubectl logs "job/${job}" > "${OUT_DIR}/${job}.log" || echo "Failed to get logs for ${job}"
  echo "Saved ${OUT_DIR}/${job}.log"
done

echo
echo "=== Cleanup sysbench CPU & memory jobs ==="
kubectl delete -f "${SYSBENCH_MANIFESTS}" 