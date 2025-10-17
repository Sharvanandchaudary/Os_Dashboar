#!/usr/bin/env python3
"""
Primary OpenStack Monitoring Dashboard
Real-time infrastructure monitoring and alerts
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.utils
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PrimaryDashboardData:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.analysis_dir = os.path.join(data_dir, 'analysis')
    
    def load_latest_metrics(self, hours=24):
        """Load latest metrics data"""
        try:
            if not os.path.exists(self.metrics_file):
                return None
            
            df = pd.read_csv(self.metrics_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter to last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            df = df[df['timestamp'] >= cutoff_time]
            
            # Calculate utilization metrics if not present
            if 'cpu_utilization' not in df.columns:
                df['cpu_utilization'] = (df['vcpus_used'] / df['vcpus_total'] * 100).fillna(0)
            if 'memory_utilization' not in df.columns:
                df['memory_utilization'] = (df['memory_used_mb'] / df['memory_total_mb'] * 100).fillna(0)
            if 'disk_utilization' not in df.columns:
                df['disk_utilization'] = (df['disk_used_gb'] / df['disk_total_gb'] * 100).fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading metrics: {str(e)}")
            return None
    
    def load_analysis(self):
        """Load latest analysis data"""
        try:
            analysis_data = {}
            
            if os.path.exists(self.analysis_dir):
                # Load node summary
                summary_files = [f for f in os.listdir(self.analysis_dir) if f.startswith('node_summary_') and f.endswith('.csv')]
                if summary_files:
                    latest_summary = sorted(summary_files)[-1]
                    summary_path = os.path.join(self.analysis_dir, latest_summary)
                    analysis_data['node_summary'] = pd.read_csv(summary_path)
                
                # Load capacity analysis
                capacity_files = [f for f in os.listdir(self.analysis_dir) if f.startswith('capacity_analysis_') and f.endswith('.json')]
                if capacity_files:
                    latest_capacity = sorted(capacity_files)[-1]
                    capacity_path = os.path.join(self.analysis_dir, latest_capacity)
                    with open(capacity_path, 'r') as f:
                        analysis_data['capacity'] = json.load(f)
                
                # Load anomalies
                anomaly_files = [f for f in os.listdir(self.analysis_dir) if f.startswith('anomalies_') and f.endswith('.json')]
                if anomaly_files:
                    latest_anomalies = sorted(anomaly_files)[-1]
                    anomaly_path = os.path.join(self.analysis_dir, latest_anomalies)
                    with open(anomaly_path, 'r') as f:
                        analysis_data['anomalies'] = json.load(f)
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Error loading analysis: {str(e)}")
            return {}

# Initialize data handler
data_handler = PrimaryDashboardData()

@app.route('/')
def index():
    """Primary dashboard page"""
    return render_template('primary_dashboard.html')

@app.route('/api/current_status')
def api_current_status():
    """API endpoint for current system status"""
    try:
        df = data_handler.load_latest_metrics(1)  # Last hour
        
        if df is None or len(df) == 0:
            return jsonify({'error': 'No recent data available'}), 404
        
        # Get latest data for each node
        latest_data = df.groupby('node').last().reset_index()
        
        # Calculate cluster summary
        cluster_summary = {
            'total_nodes': len(latest_data),
            'total_instances': int(latest_data['instances'].sum()),
            'avg_cpu_utilization': round(latest_data['cpu_utilization'].mean(), 1),
            'avg_memory_utilization': round(latest_data['memory_utilization'].mean(), 1),
            'avg_disk_utilization': round(latest_data['disk_utilization'].mean(), 1),
            'high_risk_nodes': len(latest_data[latest_data['cpu_utilization'] > 80]),
            'medium_risk_nodes': len(latest_data[(latest_data['cpu_utilization'] > 60) & (latest_data['cpu_utilization'] <= 80)]),
            'low_risk_nodes': len(latest_data[latest_data['cpu_utilization'] <= 60])
        }
        
        # Node details
        nodes = []
        for _, node in latest_data.iterrows():
            risk_level = 'High' if node['cpu_utilization'] > 80 else 'Medium' if node['cpu_utilization'] > 60 else 'Low'
            nodes.append({
                'name': node['node'],
                'cpu_utilization': round(node['cpu_utilization'], 1),
                'memory_utilization': round(node['memory_utilization'], 1),
                'disk_utilization': round(node['disk_utilization'], 1),
                'instances': int(node['instances']),
                'risk_level': risk_level,
                'status': 'Healthy' if risk_level == 'Low' else 'Warning' if risk_level == 'Medium' else 'Critical'
            })
        
        return jsonify({
            'cluster_summary': cluster_summary,
            'nodes': nodes,
            'last_update': latest_data['timestamp'].max().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in current status API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/utilization_trends')
def api_utilization_trends():
    """API endpoint for utilization trends"""
    try:
        hours = request.args.get('hours', 24, type=int)
        df = data_handler.load_latest_metrics(hours)
        
        if df is None:
            return jsonify({'error': 'No data available'}), 404
        
        # Resample to hourly data
        df_hourly = df.set_index('timestamp').groupby('node').resample('H').agg({
            'cpu_utilization': 'mean',
            'memory_utilization': 'mean',
            'disk_utilization': 'mean',
            'instances': 'mean'
        }).reset_index()
        
        trends = {
            'timestamps': df_hourly['timestamp'].dt.strftime('%Y-%m-%d %H:%M').unique().tolist(),
            'nodes': []
        }
        
        for node in df['node'].unique():
            node_data = df_hourly[df_hourly['node'] == node]
            trends['nodes'].append({
                'name': node,
                'cpu_utilization': node_data['cpu_utilization'].fillna(0).tolist(),
                'memory_utilization': node_data['memory_utilization'].fillna(0).tolist(),
                'disk_utilization': node_data['disk_utilization'].fillna(0).tolist(),
                'instances': node_data['instances'].fillna(0).tolist()
            })
        
        return jsonify(trends)
        
    except Exception as e:
        logger.error(f"❌ Error in utilization trends API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
def api_alerts():
    """API endpoint for current alerts"""
    try:
        analysis = data_handler.load_analysis()
        alerts = []
        
        # Check for high utilization
        df = data_handler.load_latest_metrics(1)
        if df is not None:
            latest_data = df.groupby('node').last().reset_index()
            
            for _, node in latest_data.iterrows():
                if node['cpu_utilization'] > 90:
                    alerts.append({
                        'type': 'Critical',
                        'node': node['node'],
                        'message': f"CPU utilization is {node['cpu_utilization']:.1f}% - immediate action required",
                        'timestamp': node['timestamp'].isoformat()
                    })
                elif node['cpu_utilization'] > 80:
                    alerts.append({
                        'type': 'Warning',
                        'node': node['node'],
                        'message': f"CPU utilization is {node['cpu_utilization']:.1f}% - monitor closely",
                        'timestamp': node['timestamp'].isoformat()
                    })
                
                if node['memory_utilization'] > 90:
                    alerts.append({
                        'type': 'Critical',
                        'node': node['node'],
                        'message': f"Memory utilization is {node['memory_utilization']:.1f}% - immediate action required",
                        'timestamp': node['timestamp'].isoformat()
                    })
        
        # Check for anomalies
        if 'anomalies' in analysis:
            for anomaly in analysis['anomalies'][:5]:  # Show last 5 anomalies
                alerts.append({
                    'type': 'Anomaly',
                    'node': anomaly['node'],
                    'message': f"Unusual {anomaly['metric']} pattern detected: {anomaly['value']:.1f}%",
                    'timestamp': anomaly['timestamp']
                })
        
        return jsonify({'alerts': alerts})
        
    except Exception as e:
        logger.error(f"❌ Error in alerts API: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory and HTML template
    os.makedirs('templates', exist_ok=True)
    
    # Create the primary dashboard HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenStack Primary Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-indicator {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .status-critical { background-color: #e74c3c; color: white; }
        .status-warning { background-color: #f39c12; color: white; }
        .status-healthy { background-color: #27ae60; color: white; }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .alert-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert-critical { background-color: #fdf2f2; border-color: #e74c3c; }
        .alert-warning { background-color: #fef9e7; border-color: #f39c12; }
        .alert-anomaly { background-color: #f0f8ff; border-color: #3498db; }
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }
        .refresh-btn:hover { background: #2980b9; }
        .loading { text-align: center; padding: 20px; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 OpenStack Primary Dashboard</h1>
        <p>Real-time Infrastructure Monitoring & Alerts</p>
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
        <button class="refresh-btn" onclick="toggleAutoRefresh()">⏰ Auto Refresh</button>
    </div>

    <div class="dashboard-grid">
        <!-- Cluster Overview -->
        <div class="card">
            <h3>📊 Cluster Overview</h3>
            <div id="cluster-summary">
                <div class="loading">Loading cluster data...</div>
            </div>
        </div>

        <!-- Current Alerts -->
        <div class="card">
            <h3>🚨 Current Alerts</h3>
            <div id="alerts-list">
                <div class="loading">Loading alerts...</div>
            </div>
        </div>

        <!-- CPU Utilization -->
        <div class="card">
            <h3>💻 CPU Utilization</h3>
            <div id="cpu-chart">
                <div class="loading">Loading CPU data...</div>
            </div>
        </div>

        <!-- Memory Utilization -->
        <div class="card">
            <h3>🧠 Memory Utilization</h3>
            <div id="memory-chart">
                <div class="loading">Loading memory data...</div>
            </div>
        </div>

        <!-- Node Status -->
        <div class="card">
            <h3>🖥️ Node Status</h3>
            <div id="node-status">
                <div class="loading">Loading node data...</div>
            </div>
        </div>

        <!-- Utilization Trends -->
        <div class="card" style="grid-column: 1 / -1;">
            <h3>📈 Utilization Trends (24 Hours)</h3>
            <div id="trends-chart">
                <div class="loading">Loading trends...</div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;

        function refreshDashboard() {
            loadClusterSummary();
            loadAlerts();
            loadNodeStatus();
            loadTrends();
        }

        function toggleAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏰ Auto Refresh';
            } else {
                autoRefreshInterval = setInterval(refreshDashboard, 30000);
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏹️ Stop Auto Refresh';
            }
        }

        async function loadClusterSummary() {
            try {
                const response = await fetch('/api/current_status');
                const data = await response.json();
                
                const summary = data.cluster_summary;
                document.getElementById('cluster-summary').innerHTML = `
                    <div class="metric-value">${summary.total_nodes}</div>
                    <div class="metric-label">Total Nodes</div>
                    <div class="metric-value">${summary.total_instances}</div>
                    <div class="metric-label">Total Instances</div>
                    <div class="metric-value">${summary.avg_cpu_utilization}%</div>
                    <div class="metric-label">Avg CPU Utilization</div>
                    <div class="metric-value">${summary.avg_memory_utilization}%</div>
                    <div class="metric-label">Avg Memory Utilization</div>
                    <div style="margin-top: 15px;">
                        <span class="status-indicator status-critical">${summary.high_risk_nodes} Critical</span>
                        <span class="status-indicator status-warning">${summary.medium_risk_nodes} Warning</span>
                        <span class="status-indicator status-healthy">${summary.low_risk_nodes} Healthy</span>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading cluster summary:', error);
            }
        }

        async function loadAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                
                const alertsHtml = data.alerts.length > 0 ? 
                    data.alerts.map(alert => `
                        <div class="alert-item alert-${alert.type.toLowerCase()}">
                            <strong>${alert.type}:</strong> ${alert.message}
                            <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                    `).join('') : 
                    '<div style="color: #27ae60; text-align: center; padding: 20px;">✅ No active alerts</div>';
                
                document.getElementById('alerts-list').innerHTML = alertsHtml;
            } catch (error) {
                console.error('Error loading alerts:', error);
            }
        }

        async function loadNodeStatus() {
            try {
                const response = await fetch('/api/current_status');
                const data = await response.json();
                
                const nodesHtml = data.nodes.map(node => `
                    <div style="padding: 10px; border-bottom: 1px solid #ecf0f1;">
                        <strong>${node.name}</strong>
                        <span class="status-indicator status-${node.status.toLowerCase()}">${node.status}</span>
                        <div style="font-size: 0.9em; color: #7f8c8d;">
                            CPU: ${node.cpu_utilization}% | Memory: ${node.memory_utilization}% | Instances: ${node.instances}
                        </div>
                    </div>
                `).join('');
                
                document.getElementById('node-status').innerHTML = nodesHtml;
            } catch (error) {
                console.error('Error loading node status:', error);
            }
        }

        async function loadTrends() {
            try {
                const response = await fetch('/api/utilization_trends');
                const data = await response.json();
                
                const traces = data.nodes.map(node => ({
                    x: data.timestamps,
                    y: node.cpu_utilization,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: node.name,
                    line: { width: 2 }
                }));
                
                const layout = {
                    title: 'CPU Utilization Trends',
                    xaxis: { title: 'Time' },
                    yaxis: { title: 'CPU Utilization (%)' },
                    hovermode: 'x unified',
                    height: 400
                };
                
                Plotly.newPlot('trends-chart', traces, layout);
            } catch (error) {
                console.error('Error loading trends:', error);
            }
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
        });
    </script>
</body>
</html>
    '''
    
    with open('templates/primary_dashboard.html', 'w') as f:
        f.write(html_template)
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"🚀 Starting Primary Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
