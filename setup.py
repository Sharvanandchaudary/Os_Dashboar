#!/usr/bin/env python3
"""
OpenStack Monitoring Dashboard Setup Script
Automated setup and configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def create_virtual_environment():
    """Create virtual environment"""
    venv_path = "openstack_monitor"
    if os.path.exists(venv_path):
        print(f"📁 Virtual environment already exists at {venv_path}")
        return True
    
    return run_command(f"python -m venv {venv_path}", "Creating virtual environment")

def install_dependencies():
    """Install required packages"""
    if os.name == 'nt':  # Windows
        pip_cmd = "openstack_monitor\\Scripts\\pip"
        python_cmd = "openstack_monitor\\Scripts\\python"
    else:  # Linux/Mac
        pip_cmd = "openstack_monitor/bin/pip"
        python_cmd = "openstack_monitor/bin/python"
    
    # Upgrade pip first
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    
    # Install requirements
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ['data', 'data/analysis', 'data/forecasts', 'templates', 'logs']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ Created {directory}/")
    
    return True

def create_config_file():
    """Create configuration file from template"""
    config_file = "config.env"
    template_file = "config.env.example"
    
    if os.path.exists(config_file):
        print(f"📄 Configuration file {config_file} already exists")
        return True
    
    if os.path.exists(template_file):
        shutil.copy(template_file, config_file)
        print(f"✅ Created {config_file} from template")
        print(f"📝 Please edit {config_file} with your OpenStack credentials")
        return True
    else:
        print(f"❌ Template file {template_file} not found")
        return False

def create_startup_scripts():
    """Create convenient startup scripts"""
    
    # Windows batch file
    if os.name == 'nt':
        batch_content = """@echo off
echo Starting OpenStack Monitoring Dashboard...
echo.
echo 1. Starting data collection...
openstack_monitor\\Scripts\\python collect_metrics.py
echo.
echo 2. Starting analysis...
openstack_monitor\\Scripts\\python analyze_metrics.py
echo.
echo 3. Starting forecasting...
openstack_monitor\\Scripts\\python forecast_usage.py
echo.
echo 4. Starting dashboard...
openstack_monitor\\Scripts\\python dashboard.py
pause
"""
        with open("start_dashboard.bat", "w") as f:
            f.write(batch_content)
        print("✅ Created start_dashboard.bat")
    
    # Unix shell script
    shell_content = """#!/bin/bash
echo "Starting OpenStack Monitoring Dashboard..."
echo ""
echo "1. Starting data collection..."
./openstack_monitor/bin/python collect_metrics.py
echo ""
echo "2. Starting analysis..."
./openstack_monitor/bin/python analyze_metrics.py
echo ""
echo "3. Starting forecasting..."
./openstack_monitor/bin/python forecast_usage.py
echo ""
echo "4. Starting dashboard..."
./openstack_monitor/bin/python dashboard.py
"""
    with open("start_dashboard.sh", "w") as f:
        f.write(shell_content)
    
    # Make shell script executable
    if os.name != 'nt':
        os.chmod("start_dashboard.sh", 0o755)
        print("✅ Created start_dashboard.sh")
    
    return True

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    
    if os.name == 'nt':  # Windows
        python_cmd = "openstack_monitor\\Scripts\\python"
    else:  # Linux/Mac
        python_cmd = "openstack_monitor/bin/python"
    
    # Test imports
    test_script = """
import sys
try:
    import requests
    import pandas
    import numpy
    import matplotlib
    import plotly
    import flask
    from prophet import Prophet
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    return run_command(f"{python_cmd} -c \"{test_script}\"", "Testing package imports")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 OpenStack Monitoring Dashboard Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Edit config.env with your OpenStack credentials")
    print("2. Test the connection:")
    if os.name == 'nt':
        print("   openstack_monitor\\Scripts\\python collect_metrics.py")
    else:
        print("   ./openstack_monitor/bin/python collect_metrics.py")
    print("3. Start the dashboard:")
    if os.name == 'nt':
        print("   start_dashboard.bat")
    else:
        print("   ./start_dashboard.sh")
    print("4. Open http://localhost:5000 in your browser")
    print("\n📚 For more information, see README.md")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 OpenStack Monitoring Dashboard Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Create config file
    if not create_config_file():
        sys.exit(1)
    
    # Create startup scripts
    if not create_startup_scripts():
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("⚠️ Installation test failed, but setup may still work")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
