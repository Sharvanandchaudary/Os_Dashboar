#!/usr/bin/env python3
"""
Start Both OpenStack Dashboards
Primary Dashboard + Forecast Dashboard
"""

import subprocess
import sys
import os
import time
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def run_primary_dashboard():
    """Run the primary monitoring dashboard"""
    print("🚀 Starting Primary Dashboard on port 5000...")
    try:
        subprocess.run([sys.executable, 'primary_dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("🛑 Primary Dashboard stopped")
    except Exception as e:
        print(f"❌ Error running Primary Dashboard: {e}")

def run_forecast_dashboard():
    """Run the forecast dashboard"""
    print("🔮 Starting Forecast Dashboard on port 5001...")
    try:
        subprocess.run([sys.executable, 'forecast_dashboard.py'], check=True)
    except KeyboardInterrupt:
        print("🛑 Forecast Dashboard stopped")
    except Exception as e:
        print(f"❌ Error running Forecast Dashboard: {e}")

def main():
    """Start both dashboards"""
    print("=" * 60)
    print("🚀 OpenStack Dual Dashboard System")
    print("=" * 60)
    print("Primary Dashboard:  http://localhost:5000")
    print("Forecast Dashboard: http://localhost:5001")
    print("=" * 60)
    print("Press Ctrl+C to stop both dashboards")
    print()
    
    # Start both dashboards in separate threads
    primary_thread = threading.Thread(target=run_primary_dashboard, daemon=True)
    forecast_thread = threading.Thread(target=run_forecast_dashboard, daemon=True)
    
    try:
        primary_thread.start()
        time.sleep(2)  # Small delay to avoid port conflicts
        forecast_thread.start()
        
        # Wait for both threads
        primary_thread.join()
        forecast_thread.join()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping both dashboards...")
        sys.exit(0)

if __name__ == "__main__":
    main()
