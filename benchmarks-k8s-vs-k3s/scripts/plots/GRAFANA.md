## Install plugin
To visualize results in Grafana, use a CSV data source plugin. For example, the Grafana CSV Plugin (e.g. marcusolsson-csv-datasource) lets you load CSV data even from a local path!
```bash
grafana-cli plugins install marcusolsson-csv-datasource
```
## Configure data source
In Grafana UI, go to Configuration ➔ Data Sources ➔ CSV. For the CSV URL, you can provide a local file path (file:///path/to/results.csv) or a URL if serving the file via HTTP. The plugin can parse the CSV into a time series or table.

**Note:** the CSV plugin treats each query as a full dataset; it doesn’t auto-store history.

## Create panels
### Time series panel
For metrics like RPS or latency over time, use the CSV data source and map a “time” column (or index) to X-axis and a “value” column to Y-axis.

```yaml
{
  "type": "timeseries",
  "title": "Request Latency",
  "targets": [{
    "datasource": "CSV",
    "csvUrl": "file:///path/to/ab_results.csv",
    "columnMapping": {"time": "timestamp", "value": "mean_latency"}
  }]
}
```

### Bar chart or gauge
For single-value metrics (e.g. average latency), you can use a Bar Gauge or Stat panel reading from CSV columns.


By using these panels, you can graph latency vs time, requests-per-second, or histograms.