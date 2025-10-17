@echo off
echo ============================================================
echo  OpenStack Monitoring Dashboard - Complete Startup
echo ============================================================
echo.

echo [1/5] Starting data collection...
start "Data Collection" cmd /k "python collect_metrics.py"

echo [2/5] Starting analysis...
start "Analysis" cmd /k "python analyze_metrics.py"

echo [3/5] Starting forecasting...
start "Forecasting" cmd /k "python forecast_usage.py"

echo [4/5] Starting Prometheus exporter...
start "Prometheus Exporter" cmd /k "python prometheus_exporter.py"

echo [5/5] Starting Prometheus...
start "Prometheus" cmd /k "prometheus --config.file=prometheus.yml --web.listen-address=0.0.0.0:9090"

echo.
echo ============================================================
echo  All services started!
echo ============================================================
echo.
echo Access URLs:
echo   Primary Dashboard:    http://localhost:5000
echo   Forecast Dashboard:   http://localhost:5001
echo   Prometheus:          http://localhost:9090
echo   Grafana:             http://localhost:3000 (admin/admin)
echo   Exporter:            http://localhost:9091/metrics
echo.
echo Press any key to open Grafana...
pause >nul

echo Opening Grafana...
start http://localhost:3000

echo.
echo Press any key to exit...
pause >nul
