#!/usr/bin/env python3
"""
Start Complete Prometheus + Grafana Stack
One command to start everything
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def run_command(command, description, wait_time=2):
    """Run a command in background"""
    print(f"🚀 Starting {description}...")
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            subprocess.Popen(command, shell=True)
        time.sleep(wait_time)
        print(f"✅ {description} started")
        return True
    except Exception as e:
        print(f"❌ Error starting {description}: {e}")
        return False

def check_port(port):
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def main():
    """Start complete Prometheus + Grafana stack"""
    print("=" * 60)
    print("🚀 Starting OpenStack Prometheus + Grafana Stack")
    print("=" * 60)
    
    # Check if ports are available
    ports_to_check = [9090, 9091, 3000]
    for port in ports_to_check:
        if check_port(port):
            print(f"⚠️ Port {port} is already in use")
    
    print("\n📋 Starting services...")
    
    # Step 1: Start data collection
    print("\n1️⃣ Starting data collection...")
    run_command("python collect_metrics.py", "Data Collection")
    run_command("python analyze_metrics.py", "Data Analysis")
    run_command("python forecast_usage.py", "Forecasting")
    
    # Step 2: Start Prometheus exporter
    print("\n2️⃣ Starting Prometheus exporter...")
    run_command("python prometheus_exporter.py", "Prometheus Exporter", 3)
    
    # Step 3: Start Prometheus
    print("\n3️⃣ Starting Prometheus...")
    if os.path.exists("prometheus.exe"):
        run_command("prometheus.exe --config.file=prometheus.yml --web.listen-address=0.0.0.0:9090", "Prometheus")
    else:
        run_command("prometheus --config.file=prometheus.yml --web.listen-address=0.0.0.0:9090", "Prometheus")
    
    # Step 4: Start Grafana
    print("\n4️⃣ Starting Grafana...")
    if os.path.exists("grafana-server.exe"):
        run_command("grafana-server.exe", "Grafana")
    else:
        run_command("grafana-server", "Grafana")
    
    # Step 5: Generate Grafana dashboards
    print("\n5️⃣ Generating Grafana dashboards...")
    run_command("python grafana_dashboards.py", "Grafana Dashboard Generator")
    
    # Wait for services to start
    print("\n⏳ Waiting for services to start...")
    time.sleep(10)
    
    # Display access information
    print("\n" + "=" * 60)
    print("🎉 All services started successfully!")
    print("=" * 60)
    print("\n📊 Access URLs:")
    print("  🔍 Prometheus:    http://localhost:9090")
    print("  📈 Grafana:       http://localhost:3000 (admin/admin)")
    print("  📡 Exporter:      http://localhost:9091/metrics")
    print("\n📋 Next Steps:")
    print("  1. Open Grafana: http://localhost:3000")
    print("  2. Login: admin/admin")
    print("  3. Add Prometheus data source: http://prometheus:9090")
    print("  4. Import dashboards from grafana_dashboards/ folder")
    print("\n🛑 To stop all services: Press Ctrl+C")
    print("=" * 60)
    
    # Open browsers
    try:
        print("\n🌐 Opening browsers...")
        webbrowser.open("http://localhost:9090")  # Prometheus
        time.sleep(2)
        webbrowser.open("http://localhost:3000")  # Grafana
    except:
        print("⚠️ Could not open browsers automatically")
    
    # Keep running
    try:
        while True:
            time.sleep(60)
            print("💓 Services running... (Press Ctrl+C to stop)")
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        print("Note: You may need to manually stop some services")

if __name__ == "__main__":
    main()
