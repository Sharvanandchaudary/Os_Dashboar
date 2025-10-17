#!/usr/bin/env python3
"""
OpenStack Prometheus Metrics Exporter
Exports OpenStack metrics to Prometheus format
"""

import os
import time
import json
import pandas as pd
from datetime import datetime
from flask import Flask, Response
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PrometheusExporter:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.analysis_dir = os.path.join(data_dir, 'analysis')
    
    def load_latest_metrics(self):
        """Load latest metrics data"""
        try:
            if not os.path.exists(self.metrics_file):
                return None
            
            df = pd.read_csv(self.metrics_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Get latest data for each node
            latest_data = df.groupby('node').last().reset_index()
            
            # Calculate utilization metrics if not present
            if 'cpu_utilization' not in latest_data.columns:
                latest_data['cpu_utilization'] = (latest_data['vcpus_used'] / latest_data['vcpus_total'] * 100).fillna(0)
            if 'memory_utilization' not in latest_data.columns:
                latest_data['memory_utilization'] = (latest_data['memory_used_mb'] / latest_data['memory_total_mb'] * 100).fillna(0)
            if 'disk_utilization' not in latest_data.columns:
                latest_data['disk_utilization'] = (latest_data['disk_used_gb'] / latest_data['disk_total_gb'] * 100).fillna(0)
            
            return latest_data
            
        except Exception as e:
            logger.error(f"❌ Error loading metrics: {str(e)}")
            return None
    
    def generate_prometheus_metrics(self):
        """Generate Prometheus format metrics"""
        try:
            df = self.load_latest_metrics()
            if df is None:
                return "# No metrics data available\n"
            
            metrics = []
            current_time = int(time.time() * 1000)  # milliseconds
            
            for _, row in df.iterrows():
                node = row['node'].replace('-', '_').replace('.', '_')
                
                # CPU metrics
                metrics.append(f"openstack_cpu_utilization_percent{{node=\"{row['node']}\"}} {row['cpu_utilization']:.2f} {current_time}")
                metrics.append(f"openstack_cpu_used{{node=\"{row['node']}\"}} {row['vcpus_used']} {current_time}")
                metrics.append(f"openstack_cpu_total{{node=\"{row['node']}\"}} {row['vcpus_total']} {current_time}")
                
                # Memory metrics
                metrics.append(f"openstack_memory_utilization_percent{{node=\"{row['node']}\"}} {row['memory_utilization']:.2f} {current_time}")
                metrics.append(f"openstack_memory_used_mb{{node=\"{row['node']}\"}} {row['memory_used_mb']} {current_time}")
                metrics.append(f"openstack_memory_total_mb{{node=\"{row['node']}\"}} {row['memory_total_mb']} {current_time}")
                
                # Disk metrics
                metrics.append(f"openstack_disk_utilization_percent{{node=\"{row['node']}\"}} {row['disk_utilization']:.2f} {current_time}")
                metrics.append(f"openstack_disk_used_gb{{node=\"{row['node']}\"}} {row['disk_used_gb']} {current_time}")
                metrics.append(f"openstack_disk_total_gb{{node=\"{row['node']}\"}} {row['disk_total_gb']} {current_time}")
                
                # Instance metrics
                metrics.append(f"openstack_instances_count{{node=\"{row['node']}\"}} {row['instances']} {current_time}")
                
                # Risk level metrics
                risk_level = 'high' if row['cpu_utilization'] > 80 else 'medium' if row['cpu_utilization'] > 60 else 'low'
                metrics.append(f"openstack_risk_level{{node=\"{row['node']}\",level=\"{risk_level}\"}} 1 {current_time}")
                
                # Node status
                status = 'up' if row.get('status', 'unknown') == 'enabled' else 'down'
                metrics.append(f"openstack_node_status{{node=\"{row['node']}\",status=\"{status}\"}} 1 {current_time}")
            
            # Add cluster-level metrics
            total_nodes = len(df)
            total_instances = df['instances'].sum()
            avg_cpu = df['cpu_utilization'].mean()
            avg_memory = df['memory_utilization'].mean()
            avg_disk = df['disk_utilization'].mean()
            
            metrics.append(f"openstack_cluster_nodes_total {total_nodes} {current_time}")
            metrics.append(f"openstack_cluster_instances_total {total_instances} {current_time}")
            metrics.append(f"openstack_cluster_cpu_utilization_avg {avg_cpu:.2f} {current_time}")
            metrics.append(f"openstack_cluster_memory_utilization_avg {avg_memory:.2f} {current_time}")
            metrics.append(f"openstack_cluster_disk_utilization_avg {avg_disk:.2f} {current_time}")
            
            return "\n".join(metrics) + "\n"
            
        except Exception as e:
            logger.error(f"❌ Error generating Prometheus metrics: {str(e)}")
            return f"# Error generating metrics: {str(e)}\n"

# Initialize exporter
exporter = PrometheusExporter()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        metrics_data = exporter.generate_prometheus_metrics()
        return Response(metrics_data, mimetype='text/plain')
    except Exception as e:
        logger.error(f"❌ Error in metrics endpoint: {str(e)}")
        return Response(f"# Error: {str(e)}\n", mimetype='text/plain')

@app.route('/health')
def health():
    """Health check endpoint"""
    return Response("OK", mimetype='text/plain')

@app.route('/')
def index():
    """Exporter info page"""
    return """
    <html>
    <head><title>OpenStack Prometheus Exporter</title></head>
    <body>
        <h1>OpenStack Prometheus Exporter</h1>
        <p>Metrics available at: <a href="/metrics">/metrics</a></p>
        <p>Health check: <a href="/health">/health</a></p>
        <h2>Available Metrics:</h2>
        <ul>
            <li>openstack_cpu_utilization_percent</li>
            <li>openstack_memory_utilization_percent</li>
            <li>openstack_disk_utilization_percent</li>
            <li>openstack_instances_count</li>
            <li>openstack_risk_level</li>
            <li>openstack_node_status</li>
            <li>openstack_cluster_*</li>
        </ul>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.getenv('PROMETHEUS_EXPORTER_PORT', 9091))
    logger.info(f"🚀 Starting Prometheus Exporter on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
