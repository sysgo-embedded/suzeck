import matplotlib.pyplot as plt
import re
import pandas as pd

# 1. Define your file path
file_path = '../../results/iperf3.log'

try:
    with open(file_path, 'r') as f:
        log_data = f.read()
except FileNotFoundError:
    print(f"Error: {file_path} not found.")
    exit()

# 2. Updated Regex for Bidirectional format
# Captures: [ID], [Role], Start, End, Transfer, TransferUnit, Bitrate, BitrateUnit, Retr (optional)
pattern = r"\[\s*(\d+)\]\[(TX-C|RX-C)\]\s+(\d+\.\d+)-(\d+\.\d+)\s+sec\s+\d+\.\d+\s+[G|M|K]Bytes\s+(\d+\.\d+)\s+(Gbits/sec|Mbits/sec)(?:\s+(\d+))?"

matches = re.findall(pattern, log_data)

# 3. Process into a DataFrame
rows = []
for m in matches:
    id_num, role, start, end, bitrate, unit, retr = m
    
    # Only keep 1-second intervals
    if float(end) - float(start) <= 1.1:
        # Convert Mbits to Gbits if necessary
        val = float(bitrate)
        if unit == "Mbits/sec":
            val = val / 1000
            
        rows.append({
            'Time': float(end),
            'Role': 'Upload (TX)' if role == 'TX-C' else 'Download (RX)',
            'Bitrate': val,
            'Retrans': int(retr) if retr else 0
        })

df = pd.DataFrame(rows)

# 4. Plotting
save_plots_dir="../../figures"
if not df.empty:
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Pivot data for easier plotting
    pivot_df = df.pivot(index='Time', columns='Role', values='Bitrate')
    
    # Plot Bitrates
    pivot_df.plot(ax=ax1, marker='o', linewidth=2)
    
    # Calculate and plot Total Throughput (combined)
    total_bw = pivot_df.sum(axis=1)
    ax1.plot(total_bw.index, total_bw, label='Total Throughput', 
             linestyle='--', color='black', alpha=0.5)

    ax1.set_xlabel('Time (sec)')
    ax1.set_ylabel('Bitrate (Gbits/sec)')
    ax1.set_title(f'Bidirectional iperf3 Network Benchmark Results')
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle=':', alpha=0.7)

    # Optional: Plot Sum of Retransmissions on right axis
    ax2 = ax1.twinx()
    retr_df = df.groupby('Time')['Retrans'].sum()
    ax2.bar(retr_df.index, retr_df.values, color='red', alpha=0.15, label='Retransmissions (Total)')
    ax2.set_ylabel('Total Retransmissions', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    fig.tight_layout()
    plt.savefig(f'{save_plots_dir}/iperf3_network_benchmark_result.png')
    
else:
    print("No bidirectional data found.")