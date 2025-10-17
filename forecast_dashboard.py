#!/usr/bin/env python3
"""
OpenStack Forecast Dashboard
ML Model Endpoint for Forecasting and Predictions
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

class ForecastDashboardData:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.forecasts_dir = os.path.join(data_dir, 'forecasts')
    
    def load_metrics(self, hours=168):  # 1 week of data
        """Load historical metrics data"""
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
    
    def load_recommendations(self):
        """Load capacity recommendations"""
        try:
            if not os.path.exists(self.forecasts_dir):
                return []
            
            # Find latest recommendations file
            rec_files = [f for f in os.listdir(self.forecasts_dir) if f.startswith('recommendations_') and f.endswith('.json')]
            if not rec_files:
                return []
            
            latest_file = sorted(rec_files)[-1]
            rec_path = os.path.join(self.forecasts_dir, latest_file)
            
            with open(rec_path, 'r') as f:
                recommendations = json.load(f)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error loading recommendations: {str(e)}")
            return []

# Initialize data handler
data_handler = ForecastDashboardData()

@app.route('/')
def index():
    """Forecast dashboard page"""
    return render_template('forecast_dashboard.html')

@app.route('/api/forecast_data')
def api_forecast_data():
    """API endpoint for forecast data"""
    try:
        # Load historical data
        historical_df = data_handler.load_metrics(168)  # 1 week
        if historical_df is None:
            return jsonify({'error': 'No historical data available'}), 404
        
        # Load forecast data
        forecast_df = data_handler.load_forecasts()
        if forecast_df is None:
            return jsonify({'error': 'No forecast data available'}), 404
        
        # Prepare data for visualization
        nodes = historical_df['node'].unique()
        metrics = ['cpu_utilization', 'memory_utilization', 'disk_utilization']
        
        data = {
            'nodes': nodes.tolist(),
            'metrics': metrics,
            'historical': {},
            'forecasts': {}
        }
        
        # Process historical data
        for node in nodes:
            node_historical = historical_df[historical_df['node'] == node]
            data['historical'][node] = {
                'timestamps': node_historical['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                'cpu_utilization': node_historical['cpu_utilization'].tolist(),
                'memory_utilization': node_historical['memory_utilization'].tolist(),
                'disk_utilization': node_historical['disk_utilization'].tolist()
            }
        
        # Process forecast data
        for node in nodes:
            for metric in metrics:
                node_forecast = forecast_df[
                    (forecast_df['node'] == node) & 
                    (forecast_df['metric'] == metric)
                ]
                
                if len(node_forecast) > 0:
                    key = f"{node}_{metric}"
                    data['forecasts'][key] = {
                        'timestamps': node_forecast['timestamp'].dt.strftime('%Y-%m-%d %H:%M').tolist(),
                        'forecast': node_forecast['forecast'].tolist(),
                        'lower_bound': node_forecast['lower_bound'].tolist(),
                        'upper_bound': node_forecast['upper_bound'].tolist()
                    }
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"❌ Error in forecast data API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model_performance')
def api_model_performance():
    """API endpoint for model performance metrics"""
    try:
        forecast_df = data_handler.load_forecasts()
        if forecast_df is None:
            return jsonify({'error': 'No forecast data available'}), 404
        
        # Calculate model performance metrics
        performance = {}
        
        for node in forecast_df['node'].unique():
            node_data = forecast_df[forecast_df['node'] == node]
            performance[node] = {}
            
            for metric in node_data['metric'].unique():
                metric_data = node_data[node_data['metric'] == metric]
                
                if 'mae' in metric_data.columns and len(metric_data) > 0:
                    performance[node][metric] = {
                        'mae': float(metric_data['mae'].iloc[0]),
                        'mape': float(metric_data['mape'].iloc[0]),
                        'rmse': float(metric_data['rmse'].iloc[0])
                    }
        
        return jsonify(performance)
        
    except Exception as e:
        logger.error(f"❌ Error in model performance API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/capacity_recommendations')
def api_capacity_recommendations():
    """API endpoint for capacity recommendations"""
    try:
        recommendations = data_handler.load_recommendations()
        
        # Categorize recommendations by severity
        categorized = {
            'critical': [r for r in recommendations if r.get('severity') == 'Critical'],
            'high': [r for r in recommendations if r.get('severity') == 'High'],
            'medium': [r for r in recommendations if r.get('severity') == 'Medium']
        }
        
        return jsonify(categorized)
        
    except Exception as e:
        logger.error(f"❌ Error in recommendations API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecast_accuracy')
def api_forecast_accuracy():
    """API endpoint for forecast accuracy analysis"""
    try:
        forecast_df = data_handler.load_forecasts()
        if forecast_df is None:
            return jsonify({'error': 'No forecast data available'}), 404
        
        # Calculate accuracy metrics
        accuracy_data = []
        
        for node in forecast_df['node'].unique():
            node_data = forecast_df[forecast_df['node'] == node]
            
            for metric in node_data['metric'].unique():
                metric_data = node_data[node_data['metric'] == metric]
                
                if len(metric_data) > 0 and 'mae' in metric_data.columns:
                    accuracy_data.append({
                        'node': node,
                        'metric': metric,
                        'mae': float(metric_data['mae'].iloc[0]),
                        'mape': float(metric_data['mape'].iloc[0]),
                        'rmse': float(metric_data['rmse'].iloc[0]),
                        'accuracy_score': max(0, 100 - float(metric_data['mape'].iloc[0]))
                    })
        
        return jsonify(accuracy_data)
        
    except Exception as e:
        logger.error(f"❌ Error in forecast accuracy API: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory and HTML template
    os.makedirs('templates', exist_ok=True)
    
    # Create the forecast dashboard HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenStack Forecast Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: linear-gradient(135deg, #8e44ad 0%, #3498db 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-selector {
            margin-bottom: 20px;
        }
        .metric-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-right: 10px;
        }
        .node-selector {
            margin-bottom: 20px;
        }
        .node-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-right: 10px;
        }
        .recommendation-item {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .rec-critical { background-color: #fdf2f2; border-color: #e74c3c; }
        .rec-high { background-color: #fef9e7; border-color: #f39c12; }
        .rec-medium { background-color: #f0f8ff; border-color: #3498db; }
        .accuracy-score {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }
        .accuracy-excellent { color: #27ae60; }
        .accuracy-good { color: #f39c12; }
        .accuracy-poor { color: #e74c3c; }
        .refresh-btn {
            background: #8e44ad;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 5px;
        }
        .refresh-btn:hover { background: #7d3c98; }
        .loading { text-align: center; padding: 20px; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 OpenStack Forecast Dashboard</h1>
        <p>ML Model Endpoint - Predictive Analytics & Capacity Planning</p>
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
        <button class="refresh-btn" onclick="toggleAutoRefresh()">⏰ Auto Refresh</button>
    </div>

    <div class="dashboard-grid">
        <!-- Model Performance -->
        <div class="card">
            <h3>📊 Model Performance</h3>
            <div id="model-performance">
                <div class="loading">Loading model performance...</div>
            </div>
        </div>

        <!-- Forecast Accuracy -->
        <div class="card">
            <h3>🎯 Forecast Accuracy</h3>
            <div id="forecast-accuracy">
                <div class="loading">Loading accuracy data...</div>
            </div>
        </div>

        <!-- Capacity Recommendations -->
        <div class="card">
            <h3>💡 Capacity Recommendations</h3>
            <div id="recommendations">
                <div class="loading">Loading recommendations...</div>
            </div>
        </div>

        <!-- Forecast Visualization -->
        <div class="card" style="grid-column: 1 / -1;">
            <h3>📈 Forecast Visualization</h3>
            <div class="metric-selector">
                <label>Metric:</label>
                <select id="metric-select" onchange="updateForecastChart()">
                    <option value="cpu_utilization">CPU Utilization</option>
                    <option value="memory_utilization">Memory Utilization</option>
                    <option value="disk_utilization">Disk Utilization</option>
                </select>
            </div>
            <div class="node-selector">
                <label>Node:</label>
                <select id="node-select" onchange="updateForecastChart()">
                    <option value="all">All Nodes</option>
                </select>
            </div>
            <div id="forecast-chart">
                <div class="loading">Loading forecast data...</div>
            </div>
        </div>
    </div>

    <script>
        let autoRefreshInterval = null;
        let forecastData = null;

        function refreshDashboard() {
            loadModelPerformance();
            loadForecastAccuracy();
            loadRecommendations();
            loadForecastData();
        }

        function toggleAutoRefresh() {
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏰ Auto Refresh';
            } else {
                autoRefreshInterval = setInterval(refreshDashboard, 60000); // 1 minute
                document.querySelector('button[onclick="toggleAutoRefresh()"]').textContent = '⏹️ Stop Auto Refresh';
            }
        }

        async function loadModelPerformance() {
            try {
                const response = await fetch('/api/model_performance');
                const data = await response.json();
                
                let performanceHtml = '';
                for (const [node, metrics] of Object.entries(data)) {
                    performanceHtml += `<h4>${node}</h4>`;
                    for (const [metric, values] of Object.entries(metrics)) {
                        performanceHtml += `
                            <div style="margin: 10px 0;">
                                <strong>${metric.replace('_', ' ').toUpperCase()}:</strong><br>
                                MAE: ${values.mae.toFixed(2)} | MAPE: ${values.mape.toFixed(2)}% | RMSE: ${values.rmse.toFixed(2)}
                            </div>
                        `;
                    }
                }
                
                document.getElementById('model-performance').innerHTML = performanceHtml;
            } catch (error) {
                console.error('Error loading model performance:', error);
            }
        }

        async function loadForecastAccuracy() {
            try {
                const response = await fetch('/api/forecast_accuracy');
                const data = await response.json();
                
                if (data.length === 0) {
                    document.getElementById('forecast-accuracy').innerHTML = '<div class="loading">No accuracy data available</div>';
                    return;
                }
                
                // Calculate average accuracy
                const avgAccuracy = data.reduce((sum, item) => sum + item.accuracy_score, 0) / data.length;
                const accuracyClass = avgAccuracy > 80 ? 'accuracy-excellent' : avgAccuracy > 60 ? 'accuracy-good' : 'accuracy-poor';
                
                document.getElementById('forecast-accuracy').innerHTML = `
                    <div class="accuracy-score ${accuracyClass}">${avgAccuracy.toFixed(1)}%</div>
                    <div style="text-align: center; color: #7f8c8d;">Average Forecast Accuracy</div>
                    <div style="margin-top: 15px;">
                        ${data.map(item => `
                            <div style="font-size: 0.9em; margin: 5px 0;">
                                ${item.node} - ${item.metric}: ${item.accuracy_score.toFixed(1)}%
                            </div>
                        `).join('')}
                    </div>
                `;
            } catch (error) {
                console.error('Error loading forecast accuracy:', error);
            }
        }

        async function loadRecommendations() {
            try {
                const response = await fetch('/api/capacity_recommendations');
                const data = await response.json();
                
                let recommendationsHtml = '';
                
                if (data.critical.length > 0) {
                    recommendationsHtml += '<h4 style="color: #e74c3c;">🚨 Critical</h4>';
                    data.critical.forEach(rec => {
                        recommendationsHtml += `
                            <div class="recommendation-item rec-critical">
                                <strong>${rec.node}</strong><br>
                                ${rec.message}<br>
                                <small>Action: ${rec.recommended_action}</small>
                            </div>
                        `;
                    });
                }
                
                if (data.high.length > 0) {
                    recommendationsHtml += '<h4 style="color: #f39c12;">⚠️ High Priority</h4>';
                    data.high.forEach(rec => {
                        recommendationsHtml += `
                            <div class="recommendation-item rec-high">
                                <strong>${rec.node}</strong><br>
                                ${rec.message}<br>
                                <small>Action: ${rec.recommended_action}</small>
                            </div>
                        `;
                    });
                }
                
                if (data.medium.length > 0) {
                    recommendationsHtml += '<h4 style="color: #3498db;">📊 Medium Priority</h4>';
                    data.medium.forEach(rec => {
                        recommendationsHtml += `
                            <div class="recommendation-item rec-medium">
                                <strong>${rec.node}</strong><br>
                                ${rec.message}<br>
                                <small>Action: ${rec.recommended_action}</small>
                            </div>
                        `;
                    });
                }
                
                if (recommendationsHtml === '') {
                    recommendationsHtml = '<div style="color: #27ae60; text-align: center; padding: 20px;">✅ No recommendations at this time</div>';
                }
                
                document.getElementById('recommendations').innerHTML = recommendationsHtml;
            } catch (error) {
                console.error('Error loading recommendations:', error);
            }
        }

        async function loadForecastData() {
            try {
                const response = await fetch('/api/forecast_data');
                const data = await response.json();
                
                forecastData = data;
                
                // Populate node selector
                const nodeSelect = document.getElementById('node-select');
                nodeSelect.innerHTML = '<option value="all">All Nodes</option>';
                data.nodes.forEach(node => {
                    nodeSelect.innerHTML += `<option value="${node}">${node}</option>`;
                });
                
                updateForecastChart();
            } catch (error) {
                console.error('Error loading forecast data:', error);
            }
        }

        function updateForecastChart() {
            if (!forecastData) return;
            
            const selectedMetric = document.getElementById('metric-select').value;
            const selectedNode = document.getElementById('node-select').value;
            
            const traces = [];
            
            if (selectedNode === 'all') {
                // Show all nodes
                forecastData.nodes.forEach(node => {
                    const historical = forecastData.historical[node];
                    if (historical) {
                        traces.push({
                            x: historical.timestamps,
                            y: historical[selectedMetric],
                            type: 'scatter',
                            mode: 'lines',
                            name: `${node} (Historical)`,
                            line: { width: 2 }
                        });
                    }
                    
                    const forecastKey = `${node}_${selectedMetric}`;
                    const forecast = forecastData.forecasts[forecastKey];
                    if (forecast) {
                        traces.push({
                            x: forecast.timestamps,
                            y: forecast.forecast,
                            type: 'scatter',
                            mode: 'lines',
                            name: `${node} (Forecast)`,
                            line: { width: 2, dash: 'dash' }
                        });
                        
                        // Add confidence interval
                        traces.push({
                            x: forecast.timestamps,
                            y: forecast.upper_bound,
                            type: 'scatter',
                            mode: 'lines',
                            line: { width: 0 },
                            showlegend: false,
                            hoverinfo: 'skip'
                        });
                        
                        traces.push({
                            x: forecast.timestamps,
                            y: forecast.lower_bound,
                            type: 'scatter',
                            mode: 'lines',
                            fill: 'tonexty',
                            fillcolor: 'rgba(0,100,80,0.2)',
                            line: { width: 0 },
                            name: `${node} (Confidence)`,
                            showlegend: false
                        });
                    }
                });
            } else {
                // Show selected node only
                const historical = forecastData.historical[selectedNode];
                if (historical) {
                    traces.push({
                        x: historical.timestamps,
                        y: historical[selectedMetric],
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Historical',
                        line: { width: 2 }
                    });
                }
                
                const forecastKey = `${selectedNode}_${selectedMetric}`;
                const forecast = forecastData.forecasts[forecastKey];
                if (forecast) {
                    traces.push({
                        x: forecast.timestamps,
                        y: forecast.forecast,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Forecast',
                        line: { width: 2, dash: 'dash' }
                    });
                    
                    // Add confidence interval
                    traces.push({
                        x: forecast.timestamps,
                        y: forecast.upper_bound,
                        type: 'scatter',
                        mode: 'lines',
                        line: { width: 0 },
                        showlegend: false,
                        hoverinfo: 'skip'
                    });
                    
                    traces.push({
                        x: forecast.timestamps,
                        y: forecast.lower_bound,
                        type: 'scatter',
                        mode: 'lines',
                        fill: 'tonexty',
                        fillcolor: 'rgba(0,100,80,0.2)',
                        line: { width: 0 },
                        name: 'Confidence Interval',
                        showlegend: false
                    });
                }
            }
            
            const layout = {
                title: `${selectedMetric.replace('_', ' ').toUpperCase()} Forecast`,
                xaxis: { title: 'Time' },
                yaxis: { title: `${selectedMetric.replace('_', ' ').toUpperCase()} (%)` },
                hovermode: 'x unified',
                height: 500
            };
            
            Plotly.newPlot('forecast-chart', traces, layout);
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
        });
    </script>
</body>
</html>
    '''
    
    with open('templates/forecast_dashboard.html', 'w') as f:
        f.write(html_template)
    
    # Get configuration
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))  # Different port for forecast dashboard
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"🔮 Starting Forecast Dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
