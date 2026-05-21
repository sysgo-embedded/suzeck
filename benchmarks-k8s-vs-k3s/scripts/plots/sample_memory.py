import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# 1. Generate Synthetic Memory Data (MB)
# K8S usually has a higher baseline overhead than K3S
np.random.seed(42)
k8s_mem = np.random.normal(650, 50, 1000) # Mean 650MB, std dev 50
k3s_mem = np.random.normal(320, 30, 1000) # Mean 320MB, std dev 30

df_mem = pd.DataFrame({
    'Memory_Usage': np.concatenate([k8s_mem, k3s_mem]),
    'System': ['K8S']*1000 + ['K3S']*1000
})

save_plots_dir="../../figures/sampled"

# --- Plot 1: Box Plot (Distribution) ---
# Good for seeing the "spread" of memory usage during the benchmark.
plt.figure(figsize=(10, 6))
sns.boxplot(
    data=df_mem,
    x='System',
    y='Memory_Usage',
    hue='System',
    palette='viridis',
    legend=False
)
plt.title('Memory Footprint Distribution')
plt.ylabel('Memory Usage (MB)')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.savefig(f'{save_plots_dir}/memory_footprint_distribution.png')

# --- Plot 2: Bar Plot (Average/Peak) ---
# Best for "at-a-glance" comparison of resource overhead.
plt.figure(figsize=(10, 6))
sns.barplot(
    data=df_mem,
    x='System',
    y='Memory_Usage',
    hue='System',
    estimator=np.mean,
    capsize=.1,
    palette='magma',
    legend=False
)
plt.title('Average Memory Usage Comparison')
plt.ylabel('Mean Memory Usage (MB)')
plt.savefig(f'{save_plots_dir}/memory_average_usage_comparison.png')