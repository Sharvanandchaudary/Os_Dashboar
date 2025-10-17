#!/usr/bin/env python3
"""
OpenStack Metrics Collector
Collects hypervisor and instance metrics from OpenStack APIs
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv('config.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpenStackCollector:
    def __init__(self):
        self.auth_url = os.getenv('OS_AUTH_URL')
        self.project_name = os.getenv('OS_PROJECT_NAME')
        self.username = os.getenv('OS_USERNAME')
        self.password = os.getenv('OS_PASSWORD')
        self.user_domain = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
        self.project_domain = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')
        
        self.token = None
        self.compute_url = None
        self.identity_url = None
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
    def authenticate(self):
        """Authenticate with OpenStack and get token"""
        try:
            auth_data = {
                "auth": {
                    "identity": {
                        "methods": ["password"],
                        "password": {
                            "user": {
                                "name": self.username,
                                "password": self.password,
                                "domain": {"name": self.user_domain}
                            }
                        }
                    },
                    "scope": {
                        "project": {
                            "name": self.project_name,
                            "domain": {"name": self.project_domain}
                        }
                    }
                }
            }
            
            response = requests.post(f"{self.auth_url}/auth/tokens", 
                                   json=auth_data,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 201:
                self.token = response.headers.get('X-Subject-Token')
                
                # Extract service URLs from catalog
                catalog = response.json()['token']['catalog']
                for service in catalog:
                    if service['type'] == 'compute':
                        for endpoint in service['endpoints']:
                            if endpoint['interface'] == 'public':
                                self.compute_url = endpoint['url']
                                break
                    elif service['type'] == 'identity':
                        for endpoint in service['endpoints']:
                            if endpoint['interface'] == 'public':
                                self.identity_url = endpoint['url']
                                break
                
                logger.info("✅ Successfully authenticated with OpenStack")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return False
    
    def get_hypervisors(self):
        """Get hypervisor details"""
        try:
            headers = {'X-Auth-Token': self.token}
            response = requests.get(f"{self.compute_url}/os-hypervisors/detail", 
                                  headers=headers)
            
            if response.status_code == 200:
                return response.json().get('hypervisors', [])
            else:
                logger.error(f"❌ Failed to get hypervisors: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting hypervisors: {str(e)}")
            return []
    
    def get_instances(self):
        """Get instance details"""
        try:
            headers = {'X-Auth-Token': self.token}
            response = requests.get(f"{self.compute_url}/servers/detail", 
                                  headers=headers)
            
            if response.status_code == 200:
                return response.json().get('servers', [])
            else:
                logger.error(f"❌ Failed to get instances: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting instances: {str(e)}")
            return []
    
    def get_flavors(self):
        """Get flavor details"""
        try:
            headers = {'X-Auth-Token': self.token}
            response = requests.get(f"{self.compute_url}/flavors/detail", 
                                  headers=headers)
            
            if response.status_code == 200:
                return response.json().get('flavors', [])
            else:
                logger.error(f"❌ Failed to get flavors: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting flavors: {str(e)}")
            return []
    
    def collect_hypervisor_metrics(self):
        """Collect hypervisor-level metrics"""
        hypervisors = self.get_hypervisors()
        instances = self.get_instances()
        flavors = self.get_flavors()
        
        # Create flavor lookup
        flavor_lookup = {f['id']: f for f in flavors}
        
        # Create instance lookup by hypervisor
        instances_by_hypervisor = {}
        for instance in instances:
            if instance.get('OS-EXT-SRV-ATTR:hypervisor_hostname'):
                hypervisor = instance['OS-EXT-SRV-ATTR:hypervisor_hostname']
                if hypervisor not in instances_by_hypervisor:
                    instances_by_hypervisor[hypervisor] = []
                instances_by_hypervisor[hypervisor].append(instance)
        
        rows = []
        timestamp = datetime.now()
        
        for hypervisor in hypervisors:
            hostname = hypervisor.get('hypervisor_hostname', 'unknown')
            
            # Calculate resource usage
            vcpus_used = hypervisor.get('vcpus_used', 0)
            vcpus_total = hypervisor.get('vcpus', 0)
            memory_used = hypervisor.get('memory_mb_used', 0)
            memory_total = hypervisor.get('memory_mb', 0)
            disk_used = hypervisor.get('local_gb_used', 0)
            disk_total = hypervisor.get('local_gb', 0)
            running_vms = hypervisor.get('running_vms', 0)
            
            # Calculate utilization percentages
            cpu_util = (vcpus_used / vcpus_total * 100) if vcpus_total > 0 else 0
            mem_util = (memory_used / memory_total * 100) if memory_total > 0 else 0
            disk_util = (disk_used / disk_total * 100) if disk_total > 0 else 0
            
            # Get instance details for this hypervisor
            hypervisor_instances = instances_by_hypervisor.get(hostname, [])
            total_instance_vcpus = 0
            total_instance_memory = 0
            
            for instance in hypervisor_instances:
                flavor_id = instance.get('flavor', {}).get('id')
                if flavor_id and flavor_id in flavor_lookup:
                    flavor = flavor_lookup[flavor_id]
                    total_instance_vcpus += flavor.get('vcpus', 0)
                    total_instance_memory += flavor.get('ram', 0)
            
            row = {
                'timestamp': timestamp,
                'node': hostname,
                'vcpus_used': vcpus_used,
                'vcpus_total': vcpus_total,
                'memory_used_mb': memory_used,
                'memory_total_mb': memory_total,
                'disk_used_gb': disk_used,
                'disk_total_gb': disk_total,
                'instances': running_vms,
                'cpu_utilization': cpu_util,
                'memory_utilization': mem_util,
                'disk_utilization': disk_util,
                'total_instance_vcpus': total_instance_vcpus,
                'total_instance_memory_mb': total_instance_memory,
                'hypervisor_type': hypervisor.get('hypervisor_type', 'unknown'),
                'hypervisor_version': hypervisor.get('hypervisor_version', 'unknown'),
                'state': hypervisor.get('state', 'unknown'),
                'status': hypervisor.get('status', 'unknown')
            }
            rows.append(row)
        
        return rows
    
    def save_metrics(self, metrics_data):
        """Save metrics to CSV file"""
        try:
            df = pd.DataFrame(metrics_data)
            
            # Append to CSV file
            csv_path = 'data/metrics.csv'
            if os.path.exists(csv_path):
                df.to_csv(csv_path, mode='a', header=False, index=False)
            else:
                df.to_csv(csv_path, index=False)
            
            # Also save as JSON for easier processing
            json_path = f"data/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_path, 'w') as f:
                json.dump(metrics_data, f, indent=2, default=str)
            
            logger.info(f"✅ Saved {len(metrics_data)} metrics records")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving metrics: {str(e)}")
            return False
    
    def cleanup_old_data(self, retention_days=30):
        """Clean up old data files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Clean up old JSON files
            for filename in os.listdir('data'):
                if filename.startswith('metrics_') and filename.endswith('.json'):
                    filepath = os.path.join('data', filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        logger.info(f"🗑️ Removed old file: {filename}")
            
            logger.info("✅ Data cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
    
    def collect_data(self):
        """Main data collection method"""
        logger.info("🚀 Starting OpenStack metrics collection...")
        
        if not self.authenticate():
            return False
        
        metrics_data = self.collect_hypervisor_metrics()
        
        if not metrics_data:
            logger.warning("⚠️ No metrics data collected")
            return False
        
        if self.save_metrics(metrics_data):
            self.cleanup_old_data()
            logger.info("✅ Data collection completed successfully")
            return True
        else:
            logger.error("❌ Failed to save metrics data")
            return False

def main():
    """Main entry point"""
    collector = OpenStackCollector()
    success = collector.collect_data()
    
    if success:
        print("✅ OpenStack metrics collection completed successfully!")
    else:
        print("❌ OpenStack metrics collection failed!")
        exit(1)

if __name__ == "__main__":
    main()
