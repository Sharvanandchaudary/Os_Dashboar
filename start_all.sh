#!/bin/bash

echo "============================================================"
echo "  OpenStack Monitoring Dashboard - Complete Startup"
echo "============================================================"
echo

echo "[1/5] Starting data collection..."
gnome-terminal --title="Data Collection" -- bash -c "python collect_metrics.py; exec bash" &

echo "[2/5] Starting analysis..."
gnome-terminal --title="Analysis" -- bash -c "python analyze_metrics.py; exec bash" &

echo "[3/5] Starting forecasting..."
gnome-terminal --title="Forecasting" -- bash -c "python forecast_usage.py; exec bash" &

echo "[4/5] Starting Prometheus exporter..."
gnome-terminal --title="Prometheus Exporter" -- bash -c "python prometheus_exporter.py; exec bash" &

echo "[5/5] Starting Prometheus..."
gnome-terminal --title="Prometheus" -- bash -c "prometheus --config.file=prometheus.yml --web.listen-address=0.0.0.0:9090; exec bash" &

echo
echo "============================================================"
echo "  All services started!"
echo "============================================================"
echo
echo "Access URLs:"
echo "  Primary Dashboard:    http://localhost:5000"
echo "  Forecast Dashboard:   http://localhost:5001"
echo "  Prometheus:          http://localhost:9090"
echo "  Grafana:             http://localhost:3000 (admin/admin)"
echo "  Exporter:            http://localhost:9091/metrics"
echo

# Make script executable
chmod +x start_all.sh

echo "Press Enter to open Grafana..."
read

echo "Opening Grafana..."
xdg-open http://localhost:3000

echo
echo "Press Enter to exit..."
read
