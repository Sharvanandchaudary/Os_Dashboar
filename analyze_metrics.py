#!/usr/bin/env python3
"""
OpenStack Metrics Analyzer
Analyzes collected metrics and generates insights
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MetricsAnalyzer:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.analysis_dir = os.path.join(data_dir, 'analysis')
        os.makedirs(self.analysis_dir, exist_ok=True)
    
    def load_metrics(self):
        """Load metrics data from CSV"""
        try:
            if not os.path.exists(self.metrics_file):
                logger.error(f"❌ Metrics file not found: {self.metrics_file}")
                return None
            
            df = pd.read_csv(self.metrics_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ Loaded {len(df)} metrics records")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading metrics: {str(e)}")
            return None
    
    def calculate_utilization_metrics(self, df):
        """Calculate additional utilization metrics"""
        df = df.copy()
        
        # Calculate utilization percentages if not already present
        if 'cpu_utilization' not in df.columns:
            df['cpu_utilization'] = (df['vcpus_used'] / df['vcpus_total'] * 100).fillna(0)
        
        if 'memory_utilization' not in df.columns:
            df['memory_utilization'] = (df['memory_used_mb'] / df['memory_total_mb'] * 100).fillna(0)
        
        if 'disk_utilization' not in df.columns:
            df['disk_utilization'] = (df['disk_used_gb'] / df['disk_total_gb'] * 100).fillna(0)
        
        # Calculate efficiency metrics
        df['cpu_efficiency'] = (df['total_instance_vcpus'] / df['vcpus_total'] * 100).fillna(0)
        df['memory_efficiency'] = (df['total_instance_memory_mb'] / df['memory_total_mb'] * 100).fillna(0)
        
        # Calculate resource waste
        df['cpu_waste'] = df['cpu_utilization'] - df['cpu_efficiency']
        df['memory_waste'] = df['memory_utilization'] - df['memory_efficiency']
        
        return df
    
    def generate_node_summary(self, df):
        """Generate summary statistics per node"""
        try:
            # Group by node and calculate statistics
            summary = df.groupby('node').agg({
                'cpu_utilization': ['mean', 'max', 'min', 'std'],
                'memory_utilization': ['mean', 'max', 'min', 'std'],
                'disk_utilization': ['mean', 'max', 'min', 'std'],
                'instances': ['mean', 'max', 'min'],
                'vcpus_total': 'first',
                'memory_total_mb': 'first',
                'disk_total_gb': 'first',
                'cpu_efficiency': 'mean',
                'memory_efficiency': 'mean',
                'cpu_waste': 'mean',
                'memory_waste': 'mean'
            }).round(2)
            
            # Flatten column names
            summary.columns = ['_'.join(col).strip() for col in summary.columns]
            summary = summary.reset_index()
            
            # Add risk assessment
            summary['cpu_risk'] = summary['cpu_utilization_mean'].apply(
                lambda x: 'High' if x > 80 else 'Medium' if x > 60 else 'Low'
            )
            summary['memory_risk'] = summary['memory_utilization_mean'].apply(
                lambda x: 'High' if x > 80 else 'Medium' if x > 60 else 'Low'
            )
            summary['disk_risk'] = summary['disk_utilization_mean'].apply(
                lambda x: 'High' if x > 80 else 'Medium' if x > 60 else 'Low'
            )
            
            # Overall risk assessment
            summary['overall_risk'] = summary.apply(
                lambda row: 'High' if any(risk == 'High' for risk in [row['cpu_risk'], row['memory_risk'], row['disk_risk']])
                else 'Medium' if any(risk == 'Medium' for risk in [row['cpu_risk'], row['memory_risk'], row['disk_risk']])
                else 'Low', axis=1
            )
            
            logger.info("✅ Generated node summary")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating node summary: {str(e)}")
            return None
    
    def generate_time_series_analysis(self, df):
        """Generate time series analysis"""
        try:
            # Resample to hourly data for better analysis
            df_hourly = df.set_index('timestamp').groupby('node').resample('H').agg({
                'cpu_utilization': 'mean',
                'memory_utilization': 'mean',
                'disk_utilization': 'mean',
                'instances': 'mean',
                'vcpus_used': 'mean',
                'memory_used_mb': 'mean',
                'disk_used_gb': 'mean'
            }).reset_index()
            
            # Calculate trends
            trends = {}
            for node in df['node'].unique():
                node_data = df_hourly[df_hourly['node'] == node].copy()
                if len(node_data) > 1:
                    # Linear regression for trend calculation
                    x = np.arange(len(node_data))
                    
                    trends[node] = {
                        'cpu_trend': np.polyfit(x, node_data['cpu_utilization'].fillna(0), 1)[0],
                        'memory_trend': np.polyfit(x, node_data['memory_utilization'].fillna(0), 1)[0],
                        'disk_trend': np.polyfit(x, node_data['disk_utilization'].fillna(0), 1)[0],
                        'data_points': len(node_data)
                    }
            
            logger.info("✅ Generated time series analysis")
            return trends
            
        except Exception as e:
            logger.error(f"❌ Error in time series analysis: {str(e)}")
            return {}
    
    def generate_capacity_analysis(self, df):
        """Generate capacity planning insights"""
        try:
            capacity_analysis = {}
            
            # Overall cluster capacity
            latest_data = df.groupby('node').last().reset_index()
            
            total_vcpus = latest_data['vcpus_total'].sum()
            total_memory = latest_data['memory_total_mb'].sum()
            total_disk = latest_data['disk_total_gb'].sum()
            
            used_vcpus = latest_data['vcpus_used'].sum()
            used_memory = latest_data['memory_used_mb'].sum()
            used_disk = latest_data['disk_used_gb'].sum()
            
            capacity_analysis['cluster'] = {
                'total_vcpus': int(total_vcpus),
                'used_vcpus': int(used_vcpus),
                'available_vcpus': int(total_vcpus - used_vcpus),
                'cpu_utilization': round(used_vcpus / total_vcpus * 100, 2),
                'total_memory_gb': round(total_memory / 1024, 2),
                'used_memory_gb': round(used_memory / 1024, 2),
                'available_memory_gb': round((total_memory - used_memory) / 1024, 2),
                'memory_utilization': round(used_memory / total_memory * 100, 2),
                'total_disk_gb': int(total_disk),
                'used_disk_gb': int(used_disk),
                'available_disk_gb': int(total_disk - used_disk),
                'disk_utilization': round(used_disk / total_disk * 100, 2),
                'total_instances': int(latest_data['instances'].sum()),
                'total_nodes': len(latest_data)
            }
            
            # Node-level capacity recommendations
            recommendations = []
            for _, node in latest_data.iterrows():
                rec = {
                    'node': node['node'],
                    'cpu_utilization': round(node['cpu_utilization'], 2),
                    'memory_utilization': round(node['memory_utilization'], 2),
                    'disk_utilization': round(node['disk_utilization'], 2),
                    'recommendations': []
                }
                
                if node['cpu_utilization'] > 80:
                    rec['recommendations'].append("Consider adding more CPU capacity or migrating instances")
                elif node['cpu_utilization'] < 20:
                    rec['recommendations'].append("CPU capacity is underutilized - consider consolidating instances")
                
                if node['memory_utilization'] > 80:
                    rec['recommendations'].append("Consider adding more memory or migrating instances")
                elif node['memory_utilization'] < 20:
                    rec['recommendations'].append("Memory capacity is underutilized - consider consolidating instances")
                
                if node['disk_utilization'] > 80:
                    rec['recommendations'].append("Consider adding more disk storage or cleaning up unused data")
                elif node['disk_utilization'] < 20:
                    rec['recommendations'].append("Disk capacity is underutilized")
                
                if not rec['recommendations']:
                    rec['recommendations'].append("Node capacity is well-balanced")
                
                recommendations.append(rec)
            
            capacity_analysis['recommendations'] = recommendations
            
            logger.info("✅ Generated capacity analysis")
            return capacity_analysis
            
        except Exception as e:
            logger.error(f"❌ Error in capacity analysis: {str(e)}")
            return {}
    
    def generate_anomaly_detection(self, df):
        """Detect anomalies in resource usage"""
        try:
            anomalies = []
            
            for node in df['node'].unique():
                node_data = df[df['node'] == node].copy()
                
                # Calculate rolling statistics
                window = min(24, len(node_data))  # 24-hour window or all data if less
                node_data['cpu_rolling_mean'] = node_data['cpu_utilization'].rolling(window=window, min_periods=1).mean()
                node_data['cpu_rolling_std'] = node_data['cpu_utilization'].rolling(window=window, min_periods=1).std()
                node_data['memory_rolling_mean'] = node_data['memory_utilization'].rolling(window=window, min_periods=1).mean()
                node_data['memory_rolling_std'] = node_data['memory_utilization'].rolling(window=window, min_periods=1).std()
                
                # Detect anomalies (values > 2 standard deviations from rolling mean)
                cpu_anomalies = node_data[
                    (node_data['cpu_utilization'] > node_data['cpu_rolling_mean'] + 2 * node_data['cpu_rolling_std']) |
                    (node_data['cpu_utilization'] < node_data['cpu_rolling_mean'] - 2 * node_data['cpu_rolling_std'])
                ]
                
                memory_anomalies = node_data[
                    (node_data['memory_utilization'] > node_data['memory_rolling_mean'] + 2 * node_data['memory_rolling_std']) |
                    (node_data['memory_utilization'] < node_data['memory_rolling_mean'] - 2 * node_data['memory_rolling_std'])
                ]
                
                for _, anomaly in cpu_anomalies.iterrows():
                    anomalies.append({
                        'timestamp': anomaly['timestamp'],
                        'node': node,
                        'metric': 'cpu_utilization',
                        'value': round(anomaly['cpu_utilization'], 2),
                        'expected_range': f"{round(anomaly['cpu_rolling_mean'] - 2*anomaly['cpu_rolling_std'], 2)} - {round(anomaly['cpu_rolling_mean'] + 2*anomaly['cpu_rolling_std'], 2)}",
                        'severity': 'High' if abs(anomaly['cpu_utilization'] - anomaly['cpu_rolling_mean']) > 3 * anomaly['cpu_rolling_std'] else 'Medium'
                    })
                
                for _, anomaly in memory_anomalies.iterrows():
                    anomalies.append({
                        'timestamp': anomaly['timestamp'],
                        'node': node,
                        'metric': 'memory_utilization',
                        'value': round(anomaly['memory_utilization'], 2),
                        'expected_range': f"{round(anomaly['memory_rolling_mean'] - 2*anomaly['memory_rolling_std'], 2)} - {round(anomaly['memory_rolling_mean'] + 2*anomaly['memory_rolling_std'], 2)}",
                        'severity': 'High' if abs(anomaly['memory_utilization'] - anomaly['memory_rolling_mean']) > 3 * anomaly['memory_rolling_std'] else 'Medium'
                    })
            
            logger.info(f"✅ Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"❌ Error in anomaly detection: {str(e)}")
            return []
    
    def save_analysis(self, node_summary, trends, capacity_analysis, anomalies):
        """Save analysis results"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save node summary
            if node_summary is not None:
                node_summary.to_csv(os.path.join(self.analysis_dir, f'node_summary_{timestamp}.csv'), index=False)
                logger.info("✅ Saved node summary")
            
            # Save trends
            with open(os.path.join(self.analysis_dir, f'trends_{timestamp}.json'), 'w') as f:
                json.dump(trends, f, indent=2, default=str)
            logger.info("✅ Saved trends analysis")
            
            # Save capacity analysis
            with open(os.path.join(self.analysis_dir, f'capacity_analysis_{timestamp}.json'), 'w') as f:
                json.dump(capacity_analysis, f, indent=2, default=str)
            logger.info("✅ Saved capacity analysis")
            
            # Save anomalies
            with open(os.path.join(self.analysis_dir, f'anomalies_{timestamp}.json'), 'w') as f:
                json.dump(anomalies, f, indent=2, default=str)
            logger.info("✅ Saved anomaly detection results")
            
            # Create summary report
            self.create_summary_report(node_summary, trends, capacity_analysis, anomalies, timestamp)
            
        except Exception as e:
            logger.error(f"❌ Error saving analysis: {str(e)}")
    
    def create_summary_report(self, node_summary, trends, capacity_analysis, anomalies, timestamp):
        """Create a human-readable summary report"""
        try:
            report_path = os.path.join(self.analysis_dir, f'summary_report_{timestamp}.txt')
            
            with open(report_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("OPENSTACK MONITORING ANALYSIS REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Cluster overview
                if capacity_analysis and 'cluster' in capacity_analysis:
                    cluster = capacity_analysis['cluster']
                    f.write("CLUSTER OVERVIEW\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Total Nodes: {cluster['total_nodes']}\n")
                    f.write(f"Total Instances: {cluster['total_instances']}\n")
                    f.write(f"CPU Utilization: {cluster['cpu_utilization']}% ({cluster['used_vcpus']}/{cluster['total_vcpus']} vCPUs)\n")
                    f.write(f"Memory Utilization: {cluster['memory_utilization']}% ({cluster['used_memory_gb']:.1f}/{cluster['total_memory_gb']:.1f} GB)\n")
                    f.write(f"Disk Utilization: {cluster['disk_utilization']}% ({cluster['used_disk_gb']}/{cluster['total_disk_gb']} GB)\n\n")
                
                # Node summary
                if node_summary is not None and len(node_summary) > 0:
                    f.write("NODE SUMMARY\n")
                    f.write("-" * 40 + "\n")
                    for _, node in node_summary.iterrows():
                        f.write(f"Node: {node['node']}\n")
                        f.write(f"  CPU Utilization: {node['cpu_utilization_mean']:.1f}% (Risk: {node['cpu_risk']})\n")
                        f.write(f"  Memory Utilization: {node['memory_utilization_mean']:.1f}% (Risk: {node['memory_risk']})\n")
                        f.write(f"  Disk Utilization: {node['disk_utilization_mean']:.1f}% (Risk: {node['disk_risk']})\n")
                        f.write(f"  Overall Risk: {node['overall_risk']}\n")
                        f.write(f"  Instances: {node['instances_mean']:.1f}\n\n")
                
                # Anomalies
                if anomalies:
                    f.write("DETECTED ANOMALIES\n")
                    f.write("-" * 40 + "\n")
                    for anomaly in anomalies[:10]:  # Show first 10 anomalies
                        f.write(f"Time: {anomaly['timestamp']}\n")
                        f.write(f"Node: {anomaly['node']}\n")
                        f.write(f"Metric: {anomaly['metric']}\n")
                        f.write(f"Value: {anomaly['value']}% (Expected: {anomaly['expected_range']}%)\n")
                        f.write(f"Severity: {anomaly['severity']}\n\n")
                    
                    if len(anomalies) > 10:
                        f.write(f"... and {len(anomalies) - 10} more anomalies\n\n")
                
                # Recommendations
                if capacity_analysis and 'recommendations' in capacity_analysis:
                    f.write("CAPACITY RECOMMENDATIONS\n")
                    f.write("-" * 40 + "\n")
                    for rec in capacity_analysis['recommendations']:
                        f.write(f"Node: {rec['node']}\n")
                        for recommendation in rec['recommendations']:
                            f.write(f"  - {recommendation}\n")
                        f.write("\n")
            
            logger.info("✅ Created summary report")
            
        except Exception as e:
            logger.error(f"❌ Error creating summary report: {str(e)}")
    
    def run_analysis(self):
        """Run complete analysis"""
        logger.info("🚀 Starting OpenStack metrics analysis...")
        
        # Load data
        df = self.load_metrics()
        if df is None:
            return False
        
        # Calculate additional metrics
        df = self.calculate_utilization_metrics(df)
        
        # Generate analyses
        node_summary = self.generate_node_summary(df)
        trends = self.generate_time_series_analysis(df)
        capacity_analysis = self.generate_capacity_analysis(df)
        anomalies = self.generate_anomaly_detection(df)
        
        # Save results
        self.save_analysis(node_summary, trends, capacity_analysis, anomalies)
        
        logger.info("✅ Analysis completed successfully")
        return True

def main():
    """Main entry point"""
    analyzer = MetricsAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("✅ OpenStack metrics analysis completed successfully!")
    else:
        print("❌ OpenStack metrics analysis failed!")
        exit(1)

if __name__ == "__main__":
    main()
