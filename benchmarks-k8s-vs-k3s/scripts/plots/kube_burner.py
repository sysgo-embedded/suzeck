import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_burner_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Extract labels into columns for easier filtering
    labels_df = pd.json_normalize(df['labels'])
    return pd.concat([df.drop('labels', axis=1), labels_df], axis=1)

def plot_comparison(metric_name, file_name):
    # Paths based on your structure
    k8s_file = os.path.join('../../benchmarks/k8s/kube-burner', file_name)
    k3s_file = os.path.join('../../benchmarks/k3s/kube-burner', file_name)

    figures_dir = os.path.abspath("../../figures/kube-burner")
    
    if not os.path.exists(k8s_file) or not os.path.exists(k3s_file):
        print(f"Skipping {metric_name}: Files not found.")
        return

    df_k8s = load_burner_json(k8s_file)
    df_k8s['cluster'] = 'K8s (Standard)'
    
    df_k3s = load_burner_json(k3s_file)
    df_k3s['cluster'] = 'K3s (Lightweight)'
    
    combined = pd.concat([df_k8s, df_k3s])
    
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=combined, x='timestamp', y='value', hue='cluster', style='mode' if 'mode' in combined.columns else None)
    plt.title(f'Comparison: {metric_name}')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{figures_dir}/{metric_name.replace(" ", "_").lower()}_comparison.png')

# 1. CPU Comparison (Focuses on System/User overhead)
plot_comparison('Node CPU Usage', 'nodeCPU.json')

# 2. Memory Comparison (Shows footprint efficiency)
plot_comparison('Node Memory Available', 'nodeMemoryAvailable.json')

# 3. API Responsiveness
plot_comparison('API Executing Requests', 'APIFlowControlCurrentExecutingRequests.json')