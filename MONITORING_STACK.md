# OpenStack Monitoring Stack - Complete Overview

## 🏗️ **Current Architecture Options**

### **Option 1: Simple Stack (Default)**
```
OpenStack APIs → Python Scripts → CSV/JSON → Flask Dashboards
```
- **Data Collection**: `collect_metrics.py`
- **Storage**: CSV files in `data/` directory
- **Analysis**: `analyze_metrics.py`
- **Forecasting**: `forecast_usage.py`
- **Dashboards**: Flask + Plotly
  - Primary Dashboard: Port 5000
  - Forecast Dashboard: Port 5001

### **Option 2: Prometheus + Grafana Stack**
```
OpenStack APIs → Prometheus Exporter → Prometheus → Grafana
```
- **Data Collection**: `collect_metrics.py` + `prometheus_exporter.py`
- **Storage**: Prometheus time-series database
- **Visualization**: Grafana dashboards
- **Ports**: 
  - Prometheus: 9090
  - Grafana: 3000
  - Exporter: 9091

## 📊 **Dashboard Parameters Explained**

### **Primary Dashboard Parameters (Port 5000)**

| Parameter | Type | Description | Thresholds | API Endpoint |
|-----------|------|-------------|------------|--------------|
| `cpu_utilization` | Float | CPU usage % per node | Critical: >80%, Warning: >60% | `/api/current_status` |
| `memory_utilization` | Float | Memory usage % per node | Critical: >80%, Warning: >60% | `/api/current_status` |
| `disk_utilization` | Float | Disk usage % per node | Critical: >80%, Warning: >60% | `/api/current_status` |
| `instances` | Integer | Running VMs per node | Node-specific limits | `/api/current_status` |
| `risk_level` | String | Critical/Warning/Healthy | Calculated from utilization | `/api/current_status` |
| `alerts` | Array | Active alerts and notifications | Real-time detection | `/api/alerts` |
| `trends` | TimeSeries | 24-hour utilization patterns | Historical data | `/api/utilization_trends` |

### **Forecast Dashboard Parameters (Port 5001)**

| Parameter | Type | Description | Confidence | API Endpoint |
|-----------|------|-------------|------------|--------------|
| `forecast_cpu` | Float | 24-hour CPU predictions | 80% confidence | `/api/forecast_data` |
| `forecast_memory` | Float | 24-hour memory predictions | 80% confidence | `/api/forecast_data` |
| `forecast_disk` | Float | 24-hour disk predictions | 80% confidence | `/api/forecast_data` |
| `confidence_interval` | Range | Upper/lower bounds | ±10% typical | `/api/forecast_data` |
| `model_accuracy` | Float | MAE, MAPE, RMSE metrics | >80% target | `/api/model_performance` |
| `recommendations` | Array | Capacity planning suggestions | AI-generated | `/api/capacity_recommendations` |

## 🔧 **Prometheus Metrics**

### **Available Metrics (if using Prometheus stack)**

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|---------|
| `openstack_cpu_utilization_percent` | Gauge | CPU utilization % | `node` |
| `openstack_memory_utilization_percent` | Gauge | Memory utilization % | `node` |
| `openstack_disk_utilization_percent` | Gauge | Disk utilization % | `node` |
| `openstack_instances_count` | Gauge | Number of instances | `node` |
| `openstack_risk_level` | Gauge | Risk level (0/1) | `node`, `level` |
| `openstack_node_status` | Gauge | Node status (0/1) | `node`, `status` |
| `openstack_cluster_nodes_total` | Gauge | Total cluster nodes | - |
| `openstack_cluster_instances_total` | Gauge | Total cluster instances | - |
| `openstack_cluster_cpu_utilization_avg` | Gauge | Average CPU utilization | - |

## 🚀 **Deployment Options**

### **1. Simple Flask Dashboards (Default)**
```bash
# Start both dashboards
python start_dashboards.py

# Access URLs
# Primary: http://localhost:5000
# Forecast: http://localhost:5001
```

### **2. Prometheus + Grafana Stack**
```bash
# Start Prometheus exporter
python prometheus_exporter.py

# Start Prometheus (separate terminal)
prometheus --config.file=prometheus.yml

# Start Grafana (separate terminal)
grafana-server

# Access URLs
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
# Exporter: http://localhost:9091/metrics
```

### **3. Docker Compose (All-in-One)**
```bash
# Start everything with Docker
docker-compose up -d

# Access URLs
# Primary Dashboard: http://localhost:5000
# Forecast Dashboard: http://localhost:5001
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

## 📈 **Grafana Dashboards**

### **Pre-built Dashboards**
- **OpenStack Monitoring**: Cluster overview, utilization trends, alerts
- **OpenStack Forecast**: ML predictions, model performance, recommendations

### **Dashboard Features**
- **Real-time Metrics**: Live data from Prometheus
- **Interactive Charts**: Zoom, pan, drill-down capabilities
- **Alerting**: Threshold-based alerts and notifications
- **Customization**: Fully customizable panels and layouts

## 🔍 **Key Monitoring Factors**

### **Infrastructure Health**
1. **CPU Utilization** - Most critical for performance
2. **Memory Utilization** - Critical for stability
3. **Disk Utilization** - Important for data safety
4. **Instance Count** - Resource allocation efficiency
5. **Node Status** - System availability

### **Predictive Analytics**
1. **24-Hour Forecasts** - Capacity planning
2. **Trend Analysis** - Growth patterns
3. **Anomaly Detection** - Unusual patterns
4. **Risk Assessment** - Proactive warnings
5. **Capacity Recommendations** - Scaling decisions

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# OpenStack Connection
OS_AUTH_URL=http://openstack:5000/v3
OS_PROJECT_NAME=admin
OS_USERNAME=admin
OS_PASSWORD=secret

# Dashboard Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Prometheus Settings
PROMETHEUS_EXPORTER_PORT=9091
```

### **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'openstack-exporter'
    static_configs:
      - targets: ['localhost:9091']
```

## 🎯 **Recommendation**

**For Production**: Use **Prometheus + Grafana** stack
- Better scalability
- Advanced alerting
- Professional visualization
- Time-series optimization

**For Development**: Use **Flask Dashboards**
- Quick setup
- Easy customization
- Lightweight
- Good for testing

## 🚀 **Quick Start Commands**

```bash
# Option 1: Simple Flask Dashboards
python start_dashboards.py

# Option 2: Prometheus + Grafana
python prometheus_exporter.py &
prometheus --config.file=prometheus.yml &
grafana-server &

# Option 3: Docker Compose
docker-compose up -d
```

Choose the monitoring stack that best fits your needs! 🎯
