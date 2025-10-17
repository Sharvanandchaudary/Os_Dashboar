# OpenStack Monitoring - Key Factors & Dashboard System

## 🔍 **Key Factors We're Monitoring**

### **Primary Infrastructure Metrics**

| Factor | Description | Critical Threshold | Warning Threshold | Impact |
|--------|-------------|-------------------|-------------------|---------|
| **CPU Utilization** | Processing power usage per node | >80% | >60% | High CPU = Performance degradation |
| **Memory Utilization** | RAM usage across nodes | >80% | >60% | High memory = System instability |
| **Disk Utilization** | Storage space consumption | >80% | >60% | High disk = Data loss risk |
| **Instance Count** | Number of running VMs per node | Node-specific | Node-specific | Over-provisioning risk |
| **Resource Efficiency** | How well resources are allocated | <70% | <50% | Resource waste |

### **Risk Assessment Matrix**

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   Factor    │    Low      │   Medium    │    High     │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ CPU Usage   │    <60%     │   60-80%    │    >80%     │
│ Memory      │    <60%     │   60-80%    │    >80%     │
│ Disk        │    <60%     │   60-80%    │    >80%     │
│ Instances   │   Normal    │   High      │  Critical   │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### **Forecasting Factors**

| Factor | Prediction Horizon | Confidence | Use Case |
|--------|-------------------|------------|----------|
| **CPU Trends** | 24 hours | 80% | Capacity planning |
| **Memory Growth** | 24 hours | 80% | Resource allocation |
| **Disk Usage** | 24 hours | 80% | Storage planning |
| **Seasonal Patterns** | 7 days | 70% | Long-term planning |
| **Anomaly Detection** | Real-time | 95% | Immediate alerts |

## 📊 **Two Dashboard System**

### 🚀 **Primary Dashboard** (Port 5000)
**Purpose**: Real-time infrastructure monitoring and alerts

**Key Features:**
- **Live Cluster Overview**: Total nodes, instances, average utilization
- **Node Health Status**: Individual node performance and risk levels
- **Active Alerts**: Critical, warning, and anomaly notifications
- **Utilization Trends**: 24-hour historical patterns
- **System Status**: Data availability and connectivity health

**What You See:**
```
┌─────────────────────────────────────────────────────────┐
│  🚀 OpenStack Primary Dashboard                        │
├─────────────────────────────────────────────────────────┤
│  📊 Cluster Overview    │  🚨 Current Alerts          │
│  • 5 Total Nodes        │  • 1 Critical Alert         │
│  • 23 Total Instances   │  • 2 Warning Alerts         │
│  • 65% Avg CPU          │  • 0 Anomalies              │
│  • 2 Critical Nodes     │                             │
├─────────────────────────────────────────────────────────┤
│  💻 CPU Utilization     │  🧠 Memory Utilization      │
│  [Live Chart]           │  [Live Chart]               │
├─────────────────────────────────────────────────────────┤
│  🖥️ Node Status         │  📈 Utilization Trends      │
│  • node1: Critical      │  [24-hour Chart]            │
│  • node2: Healthy       │                             │
│  • node3: Warning       │                             │
└─────────────────────────────────────────────────────────┘
```

### 🔮 **Forecast Dashboard** (Port 5001)
**Purpose**: ML model endpoint for predictive analytics

**Key Features:**
- **Forecast Visualization**: 24-hour ahead predictions with confidence bands
- **Model Performance**: Accuracy metrics (MAE, MAPE, RMSE)
- **Capacity Recommendations**: AI-powered scaling suggestions
- **Interactive Charts**: Historical vs predicted trends
- **Accuracy Analysis**: Model performance per node/metric

**What You See:**
```
┌─────────────────────────────────────────────────────────┐
│  🔮 OpenStack Forecast Dashboard                       │
├─────────────────────────────────────────────────────────┤
│  📊 Model Performance  │  🎯 Forecast Accuracy        │
│  • MAE: 2.3%          │  • Average: 87.5%            │
│  • MAPE: 3.1%         │  • CPU: 89.2%                │
│  • RMSE: 4.2%         │  • Memory: 85.8%             │
├─────────────────────────────────────────────────────────┤
│  💡 Capacity Recommendations                           │
│  🚨 Critical: node1 needs CPU capacity                 │
│  ⚠️ High: node3 plan memory increase                   │
│  📊 Medium: node2 monitor trends                       │
├─────────────────────────────────────────────────────────┤
│  📈 Forecast Visualization                             │
│  [Interactive Chart: Historical + 24h Forecast]       │
│  Metric: CPU Utilization | Node: All Nodes            │
└─────────────────────────────────────────────────────────┘
```

## 🎯 **Key Factors Summary**

### **What We Monitor:**
1. **CPU Utilization** - Most critical factor for performance
2. **Memory Utilization** - Critical for system stability  
3. **Disk Utilization** - Important for data safety
4. **Instance Count** - Resource allocation efficiency
5. **Resource Efficiency** - Waste detection and optimization

### **What We Predict:**
1. **24-Hour CPU Trends** - Capacity planning
2. **Memory Growth Patterns** - Resource allocation
3. **Disk Usage Projections** - Storage planning
4. **Anomaly Detection** - Immediate problem identification
5. **Capacity Recommendations** - Scaling decisions

### **Alert Thresholds:**
- **🚨 Critical**: >80% utilization (immediate action)
- **⚠️ Warning**: 60-80% utilization (monitor closely)
- **✅ Healthy**: <60% utilization (normal operation)

## 🚀 **Quick Start**

1. **Start Both Dashboards:**
```bash
python start_dashboards.py
```

2. **Access Dashboards:**
- **Primary**: http://localhost:5000 (Real-time monitoring)
- **Forecast**: http://localhost:5001 (ML predictions)

3. **Key URLs:**
- Primary Dashboard: `http://localhost:5000`
- Forecast Dashboard: `http://localhost:5001`
- Primary API: `http://localhost:5000/api/current_status`
- Forecast API: `http://localhost:5001/api/forecast_data`

## 📈 **Dashboard Workflow**

```
Data Collection → Analysis → Forecasting → Dashboards
      ↓              ↓           ↓           ↓
  collect_metrics  analyze_metrics  forecast_usage  Both Dashboards
      ↓              ↓           ↓           ↓
   CSV Storage    JSON Reports  Forecasts   Real-time UI
```

**Primary Dashboard** shows **what's happening now**  
**Forecast Dashboard** shows **what will happen next**

This dual-dashboard system gives you complete visibility into your OpenStack infrastructure - both current status and future predictions! 🚀
