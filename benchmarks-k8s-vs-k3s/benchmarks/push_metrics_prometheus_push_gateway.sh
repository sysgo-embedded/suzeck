#!/bin/bash

set -e

# Configuration
NAMESPACE="monitoring"  # pushgateway's namespace
PUSHGATEWAY_SERVICE="prometheus-prometheus-pushgateway"  # service name
LOCAL_PORT=9091
PUSHGATEWAY_URL="http://localhost:${LOCAL_PORT}/metrics/job/density-test/instance"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Pushgateway port-forward...${NC}"

# Start port-forward in background and capture its PID
kubectl port-forward -n ${NAMESPACE} svc/${PUSHGATEWAY_SERVICE} ${LOCAL_PORT}:9091 &
PORT_FORWARD_PID=$!

# Function to cleanup on exit
cleanup() {
  echo -e "\n${YELLOW}Cleaning up...${NC}"
  if [ ! -z "$PORT_FORWARD_PID" ]; then
    kill $PORT_FORWARD_PID 2>/dev/null || true
    echo -e "${GREEN}Port-forward stopped${NC}"
  fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Wait for port-forward to be ready
echo "Waiting for port-forward to be ready..."
sleep 3

# Check if port-forward is working
if ! curl -s http://localhost:${LOCAL_PORT}/metrics >/dev/null 2>&1; then
    echo -e "${RED}Error: Port-forward failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}Port-forward ready!${NC}\n"

# Find all JSON files in k3s/kube-burner and k8s/kube-burner
for instance_dir in ./k3s ./k8s; do
  if [ ! -d "${instance_dir}/kube-burner" ]; then
    echo -e "${YELLOW}Skipping ${instance_dir} - kube-burner directory not found${NC}"
    continue
  fi
    
  # Extract instance name (k3s or k8s)
  instance=$(basename "$instance_dir")
    
  echo -e "${GREEN}=== Processing ${instance} ===${NC}"
    
  # Process all JSON files in the kube-burner directory
  find "${instance_dir}/kube-burner" -type f -name "*.json" | while read json_file; do
    metric_name=$(basename "$json_file" .json)
        
    echo -e "${GREEN}  Processing: ${json_file} (metric: ${metric_name})${NC}"
        
    # Push metrics - WITHOUT timestamps (Pushgateway assigns them automatically)
      jq -r '.[] | 
      if .labels then
        "\(.metricName){\(.labels | to_entries | map("\(.key)=\"\(.value)\"") | join(","))} \(.value)"
      else
        "\(.metricName) \(.value)"
      end
    ' "${json_file}" | \
    curl -s --data-binary @- "${PUSHGATEWAY_URL}/${instance}"
      
    echo -e "${GREEN}  ✓ Pushed ${metric_name} for ${instance}${NC}"
  done
    
  echo ""
done

echo -e "${GREEN}All metrics pushed successfully!${NC}"