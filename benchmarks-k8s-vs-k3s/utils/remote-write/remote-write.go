package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/gogo/protobuf/proto"
	"github.com/golang/snappy"
	"github.com/prometheus/prometheus/prompb"
)

// KubeBurnerMetric represents a single metric from kube-burner JSON
type KubeBurnerMetric struct {
	Timestamp  string            `json:"timestamp"`
	Labels     map[string]string `json:"labels"`
	Value      float64           `json:"value"`
	MetricName string            `json:"metricName"`
	JobName    string            `json:"jobName"`
}

type PortForwardConfig struct {
	Namespace   string
	ServiceName string
	Port        string
}

func main() {

	cfg, err := parseFlags()
	if err != nil {
		log.Fatal(err)
	}

	remoteWriteMetricsURL := fmt.Sprintf("http://localhost:%s/api/v1/write", cfg.Port)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Start port-forward
	pfCmd, err := startServicePortForward(ctx, cfg)
	if err != nil {
		log.Fatalf("failed to start port-forward: %v", err)
	}
	defer func() {
		log.Println("Stopping VictoriaMetrics/Prometheus port-forward")
		cancel()
		_ = pfCmd.Wait()
	}()

	// Get absolute path -> Binary will succeed regardless of
	exePath, err := os.Executable()
	if err != nil {
		log.Fatal(err)
	}

	exeDir := filepath.Dir(exePath)

	// utils/golang/build -> go up 3 times
	repoRoot := filepath.Join(exeDir, "..", "..", "..")
	repoRoot, _ = filepath.Abs(repoRoot)

	// Process k3s and k8s directories
	for _, instance := range []string{"k3s", "k8s"} {
		kubeBurnerDir := filepath.Join(repoRoot, "benchmarks", instance, "kube-burner")

		if _, err := os.Stat(kubeBurnerDir); os.IsNotExist(err) {
			log.Printf("Skipping %s - directory not found\n", kubeBurnerDir)
			continue
		}

		log.Printf("=== Processing %s ===\n", instance)

		// Find all JSON files
		files, err := filepath.Glob(filepath.Join(kubeBurnerDir, "*.json"))
		if err != nil {
			log.Fatalf("Error finding JSON files: %v", err)
		}

		for _, file := range files {
			metricName := filepath.Base(file[:len(file)-5]) // Remove .json extension
			log.Printf("  Processing: %s (metric: %s)\n", file, metricName)

			if err := processFile(file, instance, remoteWriteMetricsURL); err != nil {
				log.Printf("  ✗ Error processing %s: %v\n", file, err)
			} else {
				log.Printf("  ✓ Pushed %s for %s\n", metricName, instance)
			}
		}
		fmt.Println()
	}

	log.Println("All metrics pushed successfully!")
}

func parseFlags() (*PortForwardConfig, error) {
	var (
		namespace   = flag.String("namespace", "monitoring", "Kubernetes namespace")
		serviceName = flag.String("service-name", "", "Service name (required)")
		remoteWrite = flag.String("remote-write", "", "Remote write target: prometheus | victoria-metrics (required)")
	)

	flag.Parse()

	if *serviceName == "" {
		log.Fatal("--service-name is required")
	}

	if *remoteWrite == "" {
		log.Fatal("--remote-write is required (prometheus | victoria-metrics)")
	}

	var port string

	switch *remoteWrite {
	case "prometheus":
		port = "9090"
	case "victoria-metrics":
		port = "8428"
	default:
		log.Fatalf("invalid --remote-write value: %s (allowed: prometheus | victoria-metrics)", *remoteWrite)
	}

	return &PortForwardConfig{
		Namespace:   *namespace,
		ServiceName: *serviceName,
		Port:        port,
	}, nil

}

func startServicePortForward(ctx context.Context, cfg *PortForwardConfig) (*exec.Cmd, error) {
	cmd := exec.CommandContext(
		ctx,
		"kubectl",
		"port-forward",
		"-n", cfg.Namespace,
		fmt.Sprintf("svc/%s", cfg.ServiceName),
		fmt.Sprintf("%s:%s", cfg.Port, cfg.Port),
	)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		return nil, err
	}

	// Wait until port-forward is ready
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		log.Println("[kubectl]", line)
		if strings.Contains(line, "Forwarding from") {
			log.Println("Prometheus port-forward ready")
			return cmd, nil
		}
	}

	return nil, fmt.Errorf(`port-forward command could not be completed. Please verify that:
    * The specified port is not already in use
    * The service name is correct and exists in the specified namespace`)
}

func processFile(filename, instance, prometheusURL string) error {
	// Read JSON file
	data, err := ioutil.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("reading file: %w", err)
	}

	// Parse JSON
	var metrics []KubeBurnerMetric
	if err := json.Unmarshal(data, &metrics); err != nil {
		return fmt.Errorf("parsing JSON: %w", err)
	}

	// Convert to Prometheus TimeSeries
	var timeSeries []prompb.TimeSeries

	for _, metric := range metrics {
		// Parse timestamp
		t, err := time.Parse(time.RFC3339Nano, metric.Timestamp)
		if err != nil {
			return fmt.Errorf("parsing timestamp: %w", err)
		}
		timestampMs := t.UnixNano() / int64(time.Millisecond)

		// Build labels
		labels := []prompb.Label{
			{Name: "__name__", Value: metric.MetricName},
			{Name: "instance", Value: instance},
			{Name: "job", Value: metric.JobName},
		}

		// Add custom labels if present
		for k, v := range metric.Labels {
			labels = append(labels, prompb.Label{Name: k, Value: v})
		}

		// Create TimeSeries
		ts := prompb.TimeSeries{
			Labels: labels,
			Samples: []prompb.Sample{
				{
					Value:     metric.Value,
					Timestamp: timestampMs,
				},
			},
		}

		timeSeries = append(timeSeries, ts)
	}

	// Create WriteRequest
	writeRequest := &prompb.WriteRequest{
		Timeseries: timeSeries,
	}

	// Marshal to protobuf
	data, err = proto.Marshal(writeRequest)
	if err != nil {
		return fmt.Errorf("marshaling protobuf: %w", err)
	}

	// Compress with snappy
	compressed := snappy.Encode(nil, data)

	// Send HTTP request
	req, err := http.NewRequest("POST", prometheusURL, bytes.NewReader(compressed))
	if err != nil {
		return fmt.Errorf("creating request: %w", err)
	}

	req.Header.Set("Content-Encoding", "snappy")
	req.Header.Set("Content-Type", "application/x-protobuf")
	req.Header.Set("X-Prometheus-Remote-Write-Version", "0.1.0")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("sending request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode/100 != 2 {
		body, _ := ioutil.ReadAll(resp.Body)
		return fmt.Errorf("bad status: %d, body: %s", resp.StatusCode, string(body))
	}

	return nil
}
