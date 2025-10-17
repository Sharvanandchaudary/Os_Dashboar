#!/usr/bin/env python3
"""
Grafana Dashboard Generator
Creates Grafana dashboards for OpenStack monitoring
"""

import json
import os
from datetime import datetime

def create_openstack_dashboard():
    """Create OpenStack monitoring dashboard for Grafana"""
    
    dashboard = {
        "dashboard": {
            "id": None,
            "title": "OpenStack Monitoring Dashboard",
            "tags": ["openstack", "monitoring"],
            "style": "dark",
            "timezone": "browser",
            "panels": [
                # Row 1: Cluster Overview
                {
                    "id": 1,
                    "title": "Cluster Overview",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Total Nodes",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "openstack_cluster_nodes_total",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 3},
                                    {"color": "red", "value": 5}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 3,
                    "title": "Total Instances",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "openstack_cluster_instances_total",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 50},
                                    {"color": "red", "value": 100}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "Avg CPU Utilization",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "openstack_cluster_cpu_utilization_avg",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "Avg Memory Utilization",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "openstack_cluster_memory_utilization_avg",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        }
                    }
                },
                
                # Row 2: CPU Utilization
                {
                    "id": 6,
                    "title": "CPU Utilization",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 9}
                },
                {
                    "id": 7,
                    "title": "CPU Utilization by Node",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_cpu_utilization_percent",
                            "refId": "A",
                            "legendFormat": "{{node}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 10},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "palette-classic"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 8,
                    "title": "CPU Heatmap",
                    "type": "heatmap",
                    "targets": [
                        {
                            "expr": "openstack_cpu_utilization_percent",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 10},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent"
                        }
                    }
                },
                
                # Row 3: Memory Utilization
                {
                    "id": 9,
                    "title": "Memory Utilization",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 18}
                },
                {
                    "id": 10,
                    "title": "Memory Utilization by Node",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_memory_utilization_percent",
                            "refId": "A",
                            "legendFormat": "{{node}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 19},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "palette-classic"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 11,
                    "title": "Memory Usage (MB)",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_memory_used_mb",
                            "refId": "A",
                            "legendFormat": "{{node}} Used"
                        },
                        {
                            "expr": "openstack_memory_total_mb",
                            "refId": "B",
                            "legendFormat": "{{node}} Total"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 19},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "MB",
                            "color": {"mode": "palette-classic"}
                        }
                    }
                },
                
                # Row 4: Disk and Instances
                {
                    "id": 12,
                    "title": "Disk and Instances",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 27}
                },
                {
                    "id": 13,
                    "title": "Disk Utilization",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_disk_utilization_percent",
                            "refId": "A",
                            "legendFormat": "{{node}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 28},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "palette-classic"},
                            "thresholds": {
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 60},
                                    {"color": "red", "value": 80}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 14,
                    "title": "Instances per Node",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_instances_count",
                            "refId": "A",
                            "legendFormat": "{{node}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 28},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"}
                        }
                    }
                },
                
                # Row 5: Node Status and Alerts
                {
                    "id": 15,
                    "title": "Node Status",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 36}
                },
                {
                    "id": 16,
                    "title": "Node Status",
                    "type": "table",
                    "targets": [
                        {
                            "expr": "openstack_node_status",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 37},
                    "fieldConfig": {
                        "defaults": {
                            "custom": {
                                "displayMode": "color-background"
                            }
                        }
                    }
                },
                {
                    "id": 17,
                    "title": "Risk Level Distribution",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "openstack_risk_level",
                            "refId": "A"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 37},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "palette-classic"}
                        }
                    }
                }
            ],
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "refresh": "30s",
            "schemaVersion": 27,
            "version": 1,
            "links": []
        }
    }
    
    return dashboard

def create_forecast_dashboard():
    """Create OpenStack forecasting dashboard for Grafana"""
    
    dashboard = {
        "dashboard": {
            "id": None,
            "title": "OpenStack Forecast Dashboard",
            "tags": ["openstack", "forecast", "ml"],
            "style": "dark",
            "timezone": "browser",
            "panels": [
                # Row 1: Forecast Overview
                {
                    "id": 1,
                    "title": "Forecast Overview",
                    "type": "row",
                    "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "CPU Forecast",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_cpu_utilization_percent",
                            "refId": "A",
                            "legendFormat": "{{node}} (Historical)"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "palette-classic"}
                        }
                    }
                },
                {
                    "id": 3,
                    "title": "Memory Forecast",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "openstack_memory_utilization_percent",
                            "refId": "A",
                            "legendFormat": "{{node}} (Historical)"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 1},
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "color": {"mode": "palette-classic"}
                        }
                    }
                }
            ],
            "time": {
                "from": "now-24h",
                "to": "now+24h"
            },
            "refresh": "1m",
            "schemaVersion": 27,
            "version": 1,
            "links": []
        }
    }
    
    return dashboard

def save_dashboards():
    """Save Grafana dashboards to JSON files"""
    try:
        # Create dashboards directory
        os.makedirs('grafana_dashboards', exist_ok=True)
        
        # Save OpenStack monitoring dashboard
        monitoring_dashboard = create_openstack_dashboard()
        with open('grafana_dashboards/openstack_monitoring.json', 'w') as f:
            json.dump(monitoring_dashboard, f, indent=2)
        
        # Save OpenStack forecast dashboard
        forecast_dashboard = create_forecast_dashboard()
        with open('grafana_dashboards/openstack_forecast.json', 'w') as f:
            json.dump(forecast_dashboard, f, indent=2)
        
        print("✅ Grafana dashboards created successfully!")
        print("📁 Files saved to:")
        print("  - grafana_dashboards/openstack_monitoring.json")
        print("  - grafana_dashboards/openstack_forecast.json")
        print("\n📋 To import in Grafana:")
        print("1. Open Grafana → Dashboards → Import")
        print("2. Upload the JSON files")
        print("3. Configure Prometheus data source")
        
    except Exception as e:
        print(f"❌ Error creating Grafana dashboards: {str(e)}")

if __name__ == "__main__":
    save_dashboards()
