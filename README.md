# OpenStack Monitoring & Forecasting Dashboard

A comprehensive monitoring and forecasting system for OpenStack infrastructure that provides real-time insights, predictive analytics, and capacity planning recommendations.

## 🚀 Features

- **Real-time Monitoring**: Collect metrics from OpenStack APIs every 15 minutes
- **Predictive Analytics**: Use Facebook Prophet for resource utilization forecasting
- **Interactive Dashboard**: Beautiful web interface with Plotly visualizations
- **Anomaly Detection**: Automatic detection of unusual resource usage patterns
- **Capacity Planning**: AI-powered recommendations for infrastructure scaling
- **Automated Scheduling**: Hands-free operation with configurable intervals

## 📊 Two Dashboard System

### 🚀 Primary Dashboard (Port 5000)
**Real-time Infrastructure Monitoring**
- **Current Status**: Live cluster overview and node health
- **Risk Assessment**: Critical/Warning/Healthy node classification
- **Active Alerts**: Real-time alerts and notifications
- **Utilization Trends**: 24-hour historical patterns
- **Node Status**: Individual node performance metrics

**Key Factors Monitored:**
- CPU Utilization (Critical >80%, Warning >60%)
- Memory Utilization (Critical >80%, Warning >60%)
- Disk Utilization (Critical >80%, Warning >60%)
- Instance Count per node
- System health and connectivity

### 🔮 Forecast Dashboard (Port 5001)
**ML Model Endpoint & Predictive Analytics**
- **Forecast Visualization**: 24-hour ahead predictions with confidence intervals
- **Model Performance**: MAE, MAPE, RMSE accuracy metrics
- **Capacity Recommendations**: AI-powered scaling suggestions
- **Forecast Accuracy**: Model performance analysis
- **Interactive Charts**: Historical vs predicted trends

**Key Forecasting Factors:**
- CPU utilization predictions (24-hour horizon)
- Memory utilization forecasts
- Disk usage projections
- Capacity constraint warnings
- Seasonal pattern analysis

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- OpenStack API access with admin credentials
- 2GB+ free disk space for data storage

### Quick Setup

1. **Clone and Setup Environment**
```bash
# Create virtual environment
python3 -m venv openstack_monitor
source openstack_monitor/bin/activate  # On Windows: openstack_monitor\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure OpenStack Connection**
```bash
# Copy and edit configuration
cp config.env.example config.env
nano config.env  # Edit with your OpenStack credentials
```

3. **Test Connection**
```bash
python collect_metrics.py
```

4. **Start Both Dashboards**
```bash
# Start both dashboards
python start_dashboards.py

# Or start individually
python primary_dashboard.py    # Port 5000
python forecast_dashboard.py   # Port 5001
```

5. **Access Dashboards**
- **Primary Dashboard**: http://localhost:5000 (Real-time monitoring)
- **Forecast Dashboard**: http://localhost:5001 (ML predictions)

## ⚙️ Configuration

### Environment Variables (`config.env`)

```bash
# OpenStack API Configuration
OS_AUTH_URL=http://your-openstack-controller:5000/v3
OS_PROJECT_NAME=admin
OS_USERNAME=admin
OS_PASSWORD=your_admin_password
OS_USER_DOMAIN_NAME=Default
OS_PROJECT_DOMAIN_NAME=Default

# Dashboard Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Data Collection Settings
COLLECTION_INTERVAL_MINUTES=15
DATA_RETENTION_DAYS=30
```

### Scheduling Options

The system supports multiple scheduling modes:

- **Manual**: Run scripts individually
- **Scheduler**: Automated background operation
- **Cron**: System-level scheduling
- **Docker**: Containerized deployment

## 📈 Usage

### Manual Data Collection
```bash
# Collect current metrics
python collect_metrics.py

# Analyze collected data
python analyze_metrics.py

# Generate forecasts
python forecast_usage.py
```

### Automated Operation
```bash
# Start scheduler (runs continuously)
python scheduler.py

# Run once and exit
python scheduler.py --run-once

# Create system service
python scheduler.py --create-service
```

### Dashboard Access
- **Main Dashboard**: http://localhost:5000
- **API Endpoints**: 
  - `/api/metrics` - Raw metrics data
  - `/api/forecasts` - Forecast data
  - `/api/analysis` - Analysis results
  - `/api/status` - System status

## 📁 Project Structure

```
openstack-dashboard/
├── collect_metrics.py      # Data collection from OpenStack APIs
├── analyze_metrics.py      # Metrics analysis and insights
├── forecast_usage.py       # Prophet-based forecasting
├── dashboard.py            # Flask web dashboard
├── scheduler.py            # Automated scheduling
├── requirements.txt        # Python dependencies
├── config.env.example     # Configuration template
├── README.md              # This file
├── data/                  # Data storage directory
│   ├── metrics.csv        # Collected metrics
│   ├── analysis/          # Analysis results
│   └── forecasts/         # Forecast data
└── templates/             # Dashboard templates
    └── dashboard.html     # Main dashboard UI
```

## 🔧 Advanced Configuration

### Custom Forecasting Parameters

Edit `forecast_usage.py` to customize:
- Forecast horizon (default: 24 hours)
- Seasonality settings
- Confidence intervals
- Model parameters

### Dashboard Customization

Modify `templates/dashboard.html` for:
- Chart layouts
- Color schemes
- Additional metrics
- Custom visualizations

### Data Retention

Configure retention policies in `scheduler.py`:
- JSON file cleanup
- CSV data pruning
- Analysis result archiving

## 📊 Monitoring & Alerts

### Built-in Monitoring
- **System Status**: Data availability indicators
- **Collection Health**: API connectivity monitoring
- **Forecast Accuracy**: Model performance tracking
- **Resource Alerts**: High utilization warnings

### Custom Alerts
Extend the system with:
- Email notifications
- Slack integration
- Webhook alerts
- Custom threshold rules

## 🚀 Deployment Options

### Local Development
```bash
python dashboard.py
```

### Production Deployment
```bash
# Using systemd (Linux)
sudo systemctl start openstack-monitor

# Using Docker
docker build -t openstack-dashboard .
docker run -p 5000:5000 openstack-dashboard

# Using Kubernetes
kubectl apply -f k8s/
```

### Cloud Deployment
- **AWS EC2**: Deploy on t3.medium+ instances
- **Azure VM**: Use B2s+ virtual machines
- **GCP Compute**: Deploy on e2-standard-2+ instances

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify OpenStack credentials
   - Check network connectivity
   - Ensure admin permissions

2. **No Data Collected**
   - Check API endpoints
   - Verify hypervisor access
   - Review collector logs

3. **Forecast Errors**
   - Ensure sufficient historical data
   - Check Prophet installation
   - Verify data quality

4. **Dashboard Not Loading**
   - Check Flask configuration
   - Verify port availability
   - Review browser console

### Log Files
- `collector.log` - Data collection logs
- `scheduler.log` - Scheduler operation logs
- `dashboard.log` - Web application logs

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=True
python dashboard.py
```

## 📚 API Reference

### Data Collection API
- **Endpoint**: OpenStack Compute API
- **Authentication**: Keystone v3
- **Data Format**: JSON/CSV
- **Frequency**: Configurable (default: 15 min)

### Dashboard API
- **Base URL**: http://localhost:5000
- **Format**: JSON
- **Authentication**: None (local access)

### Forecast API
- **Model**: Facebook Prophet
- **Input**: Historical metrics
- **Output**: Time series predictions
- **Confidence**: 80% intervals

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

## 🔄 Updates

### Version 1.0.0
- Initial release
- Basic monitoring and forecasting
- Web dashboard
- Automated scheduling

### Planned Features
- Multi-cluster support
- Advanced ML models
- Mobile dashboard
- Integration with Grafana
- Prometheus metrics export

---

**Built with ❤️ for OpenStack operators**
#   O s _ D a s h b o a r  
 