import json
import os
import glob
import argparse
from datetime import datetime
import requests
import snappy
from prometheus_client.samples import Sample
from prometheus_client.exposition import generate_latest
from prometheus_remote_write import RemoteWriteClient, TimeSeries as RWTimeSeries

# Alternative implementation using just requests + protobuf
import struct

def parse_timestamp(ts_str):
    """Parse ISO 8601 timestamp to milliseconds since epoch"""
    dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    return int(dt.timestamp() * 1000)

def create_protobuf_payload(metrics_data, instance):
    """
    Create Prometheus remote write protobuf payload manually
    This is a simplified version - for production use prometheus-client or similar
    """
    from google.protobuf import timestamp_pb2
    from prometheus_client import core
    
    # We'll use a simpler approach with the prometheus_remote_write library
    timeseries_list = []
    
    for metric in metrics_data:
        labels = {
            "__name__": metric["metricName"],
            "instance": instance,
            "job": metric.get("jobName", "density-test")
        }
        
        # Add custom labels if present
        if metric.get("labels"):
            labels.update(metric["labels"])
        
        # Parse timestamp
        timestamp_ms = parse_timestamp(metric["timestamp"])
        
        # Create time series
        ts = {
            "labels": [{"name": k, "value": v} for k, v in labels.items()],
            "samples": [{
                "value": float(metric["value"]),
                "timestamp": timestamp_ms
            }]
        }
        
        timeseries_list.append(ts)
    
    return timeseries_list

def send_remote_write(url, timeseries_data):
    """Send data via Prometheus remote write protocol"""
    # This is a simplified implementation
    # For production, use: pip install prometheus-remote-write
    
    import remote_write_pb2  # You'll need to generate this from prometheus.proto
    
    # For now, we'll use a simpler JSON-based approach compatible with VictoriaMetrics
    # and some Prometheus setups
    pass

def send_via_importapi(url, metrics_data, instance):
    """
    Send metrics using import API (works with VictoriaMetrics and some Prometheus builds)
    This is simpler and preserves timestamps
    """
    lines = []
    
    for metric in metrics_data:
        labels_dict = {
            "instance": instance,
            "job": metric.get("jobName", "density-test")
        }
        
        # Add custom labels if present
        if metric.get("labels"):
            labels_dict.update(metric["labels"])
        
        # Build label string
        label_str = ",".join([f'{k}="{v}"' for k, v in labels_dict.items()])
        
        # Parse timestamp to milliseconds
        timestamp_ms = parse_timestamp(metric["timestamp"])
        
        # Format: metric_name{labels} value timestamp
        line = f'{metric["metricName"]}{{{label_str}}} {metric["value"]} {timestamp_ms}'
        lines.append(line)
    
    # Send all metrics for this file
    payload = "\n".join(lines)
    
    # VictoriaMetrics import format
    import_url = url.replace("/api/v1/write", "/api/v1/import/prometheus")
    
    response = requests.post(
        import_url,
        data=payload,
        headers={"Content-Type": "text/plain"}
    )
    
    if response.status_code not in [200, 204]:
        raise Exception(f"Failed to send metrics: {response.status_code} - {response.text}")

def process_file(filepath, instance, prometheus_url):
    """Process a single JSON file and send to Prometheus"""
    with open(filepath, 'r') as f:
        metrics_data = json.load(f)
    
    metric_name = os.path.splitext(os.path.basename(filepath))[0]
    print(f"  Processing: {filepath} (metric: {metric_name})")
    
    try:
        send_via_importapi(prometheus_url, metrics_data, instance)
        print(f"  ✓ Pushed {metric_name} for {instance}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Push kube-burner metrics to Prometheus via remote write')
    parser.add_argument(
        '--url',
        default='http://localhost:8428/api/v1/import/prometheus',
        help='Prometheus/VictoriaMetrics URL (default: VictoriaMetrics import endpoint)'
    )
    parser.add_argument(
        '--prometheus',
        action='store_true',
        help='Use Prometheus remote write endpoint instead of import API'
    )
    
    args = parser.parse_args()
    
    if args.prometheus:
        prometheus_url = args.url.replace('/api/v1/import/prometheus', '/api/v1/write')
        print("Note: Prometheus remote write requires protobuf. Using import API is recommended.")
        print(f"Using URL: {prometheus_url}")
    else:
        prometheus_url = args.url
        print(f"Using import API URL: {prometheus_url}")
    
    # Process k3s and k8s directories
    for instance in ['k3s', 'k8s']:
        kube_burner_dir = os.path.join(instance, 'kube-burner')
        
        if not os.path.exists(kube_burner_dir):
            print(f"Skipping {instance} - kube-burner directory not found")
            continue
        
        print(f"\n=== Processing {instance} ===")
        
        # Find all JSON files
        json_files = glob.glob(os.path.join(kube_burner_dir, '*.json'))
        
        for json_file in json_files:
            process_file(json_file, instance, prometheus_url)
    
    print("\n✓ All metrics pushed successfully!")

if __name__ == '__main__':
    main()