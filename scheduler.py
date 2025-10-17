#!/usr/bin/env python3
"""
OpenStack Monitoring Scheduler
Automated scheduling for data collection, analysis, and forecasting
"""

import schedule
import time
import subprocess
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MonitoringScheduler:
    def __init__(self):
        self.collection_interval = int(os.getenv('COLLECTION_INTERVAL_MINUTES', 15))
        self.analysis_interval = 60  # Run analysis every hour
        self.forecast_interval = 240  # Run forecasting every 4 hours
        self.cleanup_interval = 1440  # Run cleanup daily
        
        # Script paths
        self.collector_script = 'collect_metrics.py'
        self.analyzer_script = 'analyze_metrics.py'
        self.forecaster_script = 'forecast_usage.py'
        
        # Ensure scripts exist
        self.validate_scripts()
    
    def validate_scripts(self):
        """Validate that all required scripts exist"""
        scripts = [self.collector_script, self.analyzer_script, self.forecaster_script]
        
        for script in scripts:
            if not os.path.exists(script):
                logger.error(f"❌ Required script not found: {script}")
                sys.exit(1)
        
        logger.info("✅ All required scripts validated")
    
    def run_script(self, script_path, description):
        """Run a Python script and log results"""
        try:
            logger.info(f"🚀 Starting {description}...")
            
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                if result.stdout:
                    logger.debug(f"Output: {result.stdout}")
            else:
                logger.error(f"❌ {description} failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"❌ Error running {description}: {str(e)}")
            return False
    
    def collect_metrics(self):
        """Collect OpenStack metrics"""
        return self.run_script(self.collector_script, "Metrics Collection")
    
    def analyze_metrics(self):
        """Analyze collected metrics"""
        return self.run_script(self.analyzer_script, "Metrics Analysis")
    
    def forecast_usage(self):
        """Generate usage forecasts"""
        return self.run_script(self.forecaster_script, "Usage Forecasting")
    
    def cleanup_old_data(self):
        """Clean up old data files"""
        try:
            logger.info("🧹 Starting data cleanup...")
            
            # Clean up old JSON files in data directory
            data_dir = 'data'
            if os.path.exists(data_dir):
                import glob
                from datetime import datetime, timedelta
                
                # Remove files older than 7 days
                cutoff_date = datetime.now() - timedelta(days=7)
                
                # Clean up old JSON files
                json_files = glob.glob(os.path.join(data_dir, '*.json'))
                for file_path in json_files:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        logger.info(f"🗑️ Removed old file: {os.path.basename(file_path)}")
                
                # Clean up old analysis files
                analysis_dir = os.path.join(data_dir, 'analysis')
                if os.path.exists(analysis_dir):
                    analysis_files = glob.glob(os.path.join(analysis_dir, '*.json'))
                    for file_path in analysis_files:
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            logger.info(f"🗑️ Removed old analysis file: {os.path.basename(file_path)}")
                
                # Clean up old forecast files
                forecasts_dir = os.path.join(data_dir, 'forecasts')
                if os.path.exists(forecasts_dir):
                    forecast_files = glob.glob(os.path.join(forecasts_dir, '*.json'))
                    for file_path in forecast_files:
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            logger.info(f"🗑️ Removed old forecast file: {os.path.basename(file_path)}")
            
            logger.info("✅ Data cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
            return False
    
    def setup_schedule(self):
        """Set up the scheduling jobs"""
        try:
            # Clear existing jobs
            schedule.clear()
            
            # Data collection - every N minutes
            schedule.every(self.collection_interval).minutes.do(self.collect_metrics)
            logger.info(f"📅 Scheduled metrics collection every {self.collection_interval} minutes")
            
            # Analysis - every hour
            schedule.every().hour.do(self.analyze_metrics)
            logger.info("📅 Scheduled metrics analysis every hour")
            
            # Forecasting - every 4 hours
            schedule.every(4).hours.do(self.forecast_usage)
            logger.info("📅 Scheduled usage forecasting every 4 hours")
            
            # Cleanup - daily at 2 AM
            schedule.every().day.at("02:00").do(self.cleanup_old_data)
            logger.info("📅 Scheduled data cleanup daily at 2:00 AM")
            
            logger.info("✅ All jobs scheduled successfully")
            
        except Exception as e:
            logger.error(f"❌ Error setting up schedule: {str(e)}")
            return False
        
        return True
    
    def run_initial_tasks(self):
        """Run initial tasks on startup"""
        logger.info("🚀 Running initial tasks...")
        
        # Run initial data collection
        if not self.collect_metrics():
            logger.warning("⚠️ Initial data collection failed")
        
        # Run initial analysis
        if not self.analyze_metrics():
            logger.warning("⚠️ Initial analysis failed")
        
        # Run initial forecasting
        if not self.forecast_usage():
            logger.warning("⚠️ Initial forecasting failed")
        
        logger.info("✅ Initial tasks completed")
    
    def start_scheduler(self):
        """Start the scheduler"""
        try:
            logger.info("🚀 Starting OpenStack Monitoring Scheduler...")
            logger.info(f"Collection interval: {self.collection_interval} minutes")
            logger.info(f"Analysis interval: {self.analysis_interval} minutes")
            logger.info(f"Forecast interval: {self.forecast_interval} minutes")
            logger.info(f"Cleanup interval: {self.cleanup_interval} minutes")
            
            # Setup schedule
            if not self.setup_schedule():
                logger.error("❌ Failed to setup schedule")
                return False
            
            # Run initial tasks
            self.run_initial_tasks()
            
            # Main scheduler loop
            logger.info("⏰ Scheduler started - press Ctrl+C to stop")
            
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            return True
        except Exception as e:
            logger.error(f"❌ Scheduler error: {str(e)}")
            return False

def create_systemd_service():
    """Create a systemd service file for Linux systems"""
    service_content = f"""[Unit]
Description=OpenStack Monitoring Scheduler
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'openstack')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'scheduler.py')}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = 'openstack-monitor.service'
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Created systemd service file: {service_file}")
    print("To install:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable openstack-monitor")
    print("  sudo systemctl start openstack-monitor")

def create_windows_service():
    """Create a Windows service script"""
    service_script = '''@echo off
echo Starting OpenStack Monitoring Scheduler...
python scheduler.py
pause
'''
    
    with open('start_scheduler.bat', 'w') as f:
        f.write(service_script)
    
    print("✅ Created Windows batch file: start_scheduler.bat")
    print("Run this file to start the scheduler on Windows")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenStack Monitoring Scheduler')
    parser.add_argument('--create-service', action='store_true', 
                       help='Create system service files')
    parser.add_argument('--run-once', action='store_true',
                       help='Run all tasks once and exit')
    
    args = parser.parse_args()
    
    if args.create_service:
        if os.name == 'nt':  # Windows
            create_windows_service()
        else:  # Linux/Unix
            create_systemd_service()
        return
    
    scheduler = MonitoringScheduler()
    
    if args.run_once:
        logger.info("🚀 Running all tasks once...")
        scheduler.run_initial_tasks()
        logger.info("✅ One-time execution completed")
    else:
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()
