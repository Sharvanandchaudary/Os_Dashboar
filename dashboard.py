#!/usr/bin/env python3
"""
OpenStack Monitoring Dashboard
Flask web application with Plotly visualizations
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

class DashboardData:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.forecasts_dir = os.path.join(data_dir, 'forecasts')
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
    
    def load_forecasts(self):
        """Load latest forecast data"""
        try:
            if not os.path.exists(self.forecasts_dir):
                return None
            
            # Find latest forecast file
            forecast_files = [f for f in os.listdir(self.forecasts_dir) if f.startswith('forecasts_') and f.endswith('.csv')]
            if not forecast_files:
                return None
            
            latest_file = sorted(forecast_files)[-1]
            forecast_path = os.path.join(self.forecasts_dir, latest_file)
            
            df = pd.read_csv(forecast_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading forecasts: {str(e)}")
            return None
    
    def load_analysis(self):
        """Load latest analysis data"""
        try:
            analysis_data = {}
            
            # Load node summary
            if os.path.exists(self.analysis_dir):
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
data_handler = DashboardData()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for metrics data"""
    try:
        hours = request.args.get('hours', 24, type=int)
        df = data_handler.load_latest_metrics(hours)
        
        if df is None:
            return jsonify({'error': 'No metrics data available'}), 404
        
        # Convert to JSON-serializable format
        data = {
            'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'nodes': df['node'].unique().tolist(),
            'metrics': []
        }
        
        for node in data['nodes']:
            node_data = df[df['node'] == node]
            data['metrics'].append({
                'node': node,
                'timestamps': node_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'cpu_utilization': node_data['cpu_utilization'].tolist(),
                'memory_utilization': node_data['memory_utilization'].tolist(),
                'disk_utilization': node_data['disk_utilization'].tolist(),
                'instances': node_data['instances'].tolist()
            })
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"❌ Error in metrics API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecasts')
def api_forecasts():
    """API endpoint for forecast data"""
    try:
        df = data_handler.load_forecasts()
        
        if df is None:
            return jsonify({'error': 'No forecast data available'}), 404
        
        # Convert to JSON-serializable format
        data = {
            'timestamps': df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            'nodes': df['node'].unique().tolist(),
            'metrics': df['metric'].unique().tolist(),
            'forecasts': []
        }
        
        for node in data['nodes']:
            for metric in data['metrics']:
                forecast_data = df[(df['node'] == node) & (df['metric'] == metric)]
                if len(forecast_data) > 0:
                    data['forecasts'].append({
                        'node': node,
                        'metric': metric,
                        'timestamps': forecast_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                        'forecast': forecast_data['forecast'].tolist(),
                        'lower_bound': forecast_data['lower_bound'].tolist(),
                        'upper_bound': forecast_data['upper_bound'].tolist()
                    })
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"❌ Error in forecasts API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis')
def api_analysis():
    """API endpoint for analysis data"""
    try:
        analysis = data_handler.load_analysis()
        
        if not analysis:
            return jsonify({'error': 'No analysis data available'}), 404
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"❌ Error in analysis API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    try:
        status = {
            'timestamp': datetime.now().isoformat(),
            'data_available': {
                'metrics': os.path.exists(data_handler.metrics_file),
                'forecasts': os.path.exists(data_handler.forecasts_dir) and len(os.listdir(data_handler.forecasts_dir)) > 0,
                'analysis': os.path.exists(data_handler.analysis_dir) and len(os.listdir(data_handler.analysis_dir)) > 0
            },
            'last_update': None
        }
        
        # Get last update time from metrics file
        if os.path.exists(data_handler.metrics_file):
            status['last_update'] = datetime.fromtimestamp(
                os.path.getmtime(data_handler.metrics_file)
            ).isoformat()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Error in status API: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_utilization_chart(df, metric, title):
    """Create utilization chart"""
    fig = go.Figure()
    
    for node in df['node'].unique():
        node_data = df[df['node'] == node]
        fig.add_trace(go.Scatter(
            x=node_data['timestamp'],
            y=node_data[metric],
            mode='lines+markers',
            name=node,
            line=dict(width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title=f'{metric.replace("_", " ").title()} (%)',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_heatmap_chart(df, metric, title):
    """Create heatmap chart"""
    # Pivot data for heatmap
    pivot_data = df.pivot_table(
        values=metric,
        index='node',
        columns=df['timestamp'].dt.floor('H'),
        aggfunc='mean'
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns.strftime('%H:%M'),
        y=pivot_data.index,
        colorscale='RdYlBu_r',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Hour',
        yaxis_title='Node',
        template='plotly_white',
        height=400
    )
    
    return fig

@app.route('/charts/utilization')
def charts_utilization():
    """Generate utilization charts"""
    try:
        df = data_handler.load_latest_metrics(24)
        
        if df is None:
            return jsonify({'error': 'No data available'}), 404
        
        charts = {}
        
        # CPU utilization
        charts['cpu'] = create_utilization_chart(
            df, 'cpu_utilization', 'CPU Utilization Over Time'
        ).to_json()
        
        # Memory utilization
        charts['memory'] = create_utilization_chart(
            df, 'memory_utilization', 'Memory Utilization Over Time'
        ).to_json()
        
        # Disk utilization
        charts['disk'] = create_utilization_chart(
            df, 'disk_utilization', 'Disk Utilization Over Time'
        ).to_json()
        
        return jsonify(charts)
        
    except Exception as e:
        logger.error(f"❌ Error creating utilization charts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/charts/heatmap')
def charts_heatmap():
    """Generate heatmap charts"""
    try:
        df = data_handler.load_latest_metrics(24)
        
        if df is None:
            return jsonify({'error': 'No data available'}), 404
        
        charts = {}
        
        # CPU heatmap
        charts['cpu'] = create_heatmap_chart(
            df, 'cpu_utilization', 'CPU Utilization Heatmap'
        ).to_json()
        
        # Memory heatmap
        charts['memory'] = create_heatmap_chart(
            df, 'memory_utilization', 'Memory Utilization Heatmap'
        ).to_json()
        
        return jsonify(charts)
        
    except Exception as e:
        logger.error(f"❌ Error creating heatmap charts: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory and HTML template
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenStack Monitoring Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-panel {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .status-item:last-child {
            border-bottom: none;
        }
        .status-indicator {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-ok {
            background-color: #d4edda;
            color: #155724;
        }
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 OpenStack Monitoring Dashboard</h1>
        <p>Real-time monitoring and forecasting for OpenStack infrastructure</p>
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Data</button>
        <button class="refresh-btn" onclick="toggleAutoRefresh()">⏰ Auto Refresh</button>
    </div>

    <div class="status-panel">
        <h3>📊 System Status</h3>
        <div id="status-content">
            <div class="loading">Loading status...</div>
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="chart-container">
            <h3>💻 CPU Utilization</h3>
            <div id="cpu-chart">
                <div class="loading">Loading CPU data...</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>🧠 Memory Utilization</h3>
            <div id="memory-chart">
                <div class="loading">Loading memory data...</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>💾 Disk Utilization</h3>
            <div id="disk-chart">
                <div class="loading">Loading disk data...</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>📈 CPU Heatmap</h3>
            <div id="cpu-heatmap">
                <div class="loading">Loading CPU heatmap...</div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;

        function refreshDashboard() {
            loadStatus();
            loadCharts();
        }

        function toggleAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏰ Auto Refresh';
            } else {
                autoRefreshInterval = setInterval(refreshDashboard, 30000); // 30 seconds
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏹️ Stop Auto Refresh';
            }
        }

        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                const statusContent = document.getElementById('status-content');
                statusContent.innerHTML = `
                    <div class="status-item">
                        <span>Last Update:</span>
                        <span>${status.last_update ? new Date(status.last_update).toLocaleString() : 'Unknown'}</span>
                    </div>
                    <div class="status-item">
                        <span>Metrics Data:</span>
                        <span class="status-indicator ${status.data_available.metrics ? 'status-ok' : 'status-error'}">
                            ${status.data_available.metrics ? 'Available' : 'Not Available'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span>Forecast Data:</span>
                        <span class="status-indicator ${status.data_available.forecasts ? 'status-ok' : 'status-error'}">
                            ${status.data_available.forecasts ? 'Available' : 'Not Available'}
                        </span>
                    </div>
                    <div class="status-item">
                        <span>Analysis Data:</span>
                        <span class="status-indicator ${status.data_available.analysis ? 'status-ok' : 'status-error'}">
                            ${status.data_available.analysis ? 'Available' : 'Not Available'}
                        </span>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading status:', error);
                document.getElementById('status-content').innerHTML = '<div class="status-error">Error loading status</div>';
            }
        }

        async function loadCharts() {
            try {
                // Load utilization charts
                const chartsResponse = await fetch('/charts/utilization');
                const charts = await chartsResponse.json();
                
                if (charts.cpu) {
                    Plotly.newPlot('cpu-chart', JSON.parse(charts.cpu).data, JSON.parse(charts.cpu).layout);
                }
                
                if (charts.memory) {
                    Plotly.newPlot('memory-chart', JSON.parse(charts.memory).data, JSON.parse(charts.memory).layout);
                }
                
                if (charts.disk) {
                    Plotly.newPlot('disk-chart', JSON.parse(charts.disk).data, JSON.parse(charts.disk).layout);
                }

                // Load heatmap charts
                const heatmapResponse = await fetch('/charts/heatmap');
                const heatmaps = await heatmapResponse.json();
                
                if (heatmaps.cpu) {
                    Plotly.newPlot('cpu-heatmap', JSON.parse(heatmaps.cpu).data, JSON.parse(heatmaps.cpu).layout);
                }
                
            } catch (error) {
                console.error('Error loading charts:', error);
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
    
    with open('templates/dashboard.html', 'w') as f:
        f.write(html_template)
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"🚀 Starting OpenStack Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
