import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Generate Synthetic Raw Latency (Based on your summary stats)
np.random.seed(42)
k8s_samples = np.concatenate([np.random.normal(1.0, 0.2, 900), np.random.uniform(1.5, 5.0, 95), [25.55]*5])
k3s_samples = np.concatenate([np.random.normal(0.9, 0.15, 900), np.random.uniform(1.2, 3.0, 95), [15.30]*5])

df_raw = pd.DataFrame({
    'Latency': np.concatenate([k8s_samples, k3s_samples]),
    'System': ['K8S']*1000 + ['K3S']*1000
})

save_plots_dir="../../figures/sampled"

# ECDF Plot
# The ECDF shows the probability that a request will be completed within a certain time.
# Best for: Visualizing consistency and "Tail Latency."
# Interpretation: A curve that stays to the left indicates a faster
# system. The point where the curve flattens out shows your 95th and 99th percentiles.
plt.figure(figsize=(10, 5))
sns.ecdfplot(data=df_raw, x='Latency', hue='System')
plt.xscale('log')
plt.title('CPU Consistency and Tail Latency')
plt.xlabel(r'Latency ($ms$) - Log Scale')
plt.savefig(f'{save_plots_dir}/cpu_consistency_and_tail_latency.png')

# Box Plot
# This plot summarizes the data distribution by showing the median, quartiles, and individual outliers.
# Best for: Comparing variability.
# Interpretation: The "box" contains the middle $50\%$ of the data. The "dots" (outliers) clearly show
# the maximum latency spikes you provided ($25.55\text{ }ms$ for K8S).
plt.figure(figsize=(10, 5))
sns.boxplot(data=df_raw, x='System', y='Latency', hue='System')
plt.yscale('log')
plt.title('CPU Latency Distribution')
plt.ylabel(r'Latency ($ms$)')
plt.savefig(f'{save_plots_dir}/cpu_latency_distribution.png')
