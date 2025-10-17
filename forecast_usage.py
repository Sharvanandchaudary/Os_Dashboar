#!/usr/bin/env python3
"""
OpenStack Usage Forecaster
Uses Prophet to forecast resource utilization trends
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UsageForecaster:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, 'metrics.csv')
        self.forecasts_dir = os.path.join(data_dir, 'forecasts')
        os.makedirs(self.forecasts_dir, exist_ok=True)
    
    def load_metrics(self):
        """Load metrics data from CSV"""
        try:
            if not os.path.exists(self.metrics_file):
                logger.error(f"❌ Metrics file not found: {self.metrics_file}")
                return None
            
            df = pd.read_csv(self.metrics_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Calculate utilization metrics if not present
            if 'cpu_utilization' not in df.columns:
                df['cpu_utilization'] = (df['vcpus_used'] / df['vcpus_total'] * 100).fillna(0)
            if 'memory_utilization' not in df.columns:
                df['memory_utilization'] = (df['memory_used_mb'] / df['memory_total_mb'] * 100).fillna(0)
            if 'disk_utilization' not in df.columns:
                df['disk_utilization'] = (df['disk_used_gb'] / df['disk_total_gb'] * 100).fillna(0)
            
            logger.info(f"✅ Loaded {len(df)} metrics records")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error loading metrics: {str(e)}")
            return None
    
    def prepare_prophet_data(self, df, node, metric):
        """Prepare data for Prophet forecasting"""
        try:
            # Filter data for specific node and metric
            node_data = df[df['node'] == node].copy()
            if len(node_data) < 10:  # Need minimum data points
                return None
            
            # Prepare Prophet format (ds, y)
            prophet_data = node_data[['timestamp', metric]].copy()
            prophet_data.columns = ['ds', 'y']
            prophet_data = prophet_data.dropna()
            
            # Remove outliers (values > 3 standard deviations)
            mean_val = prophet_data['y'].mean()
            std_val = prophet_data['y'].std()
            prophet_data = prophet_data[
                (prophet_data['y'] >= mean_val - 3 * std_val) & 
                (prophet_data['y'] <= mean_val + 3 * std_val)
            ]
            
            if len(prophet_data) < 5:
                return None
            
            return prophet_data
            
        except Exception as e:
            logger.error(f"❌ Error preparing Prophet data for {node} {metric}: {str(e)}")
            return None
    
    def create_prophet_model(self, seasonality_mode='additive', changepoint_prior_scale=0.05):
        """Create and configure Prophet model"""
        try:
            model = Prophet(
                seasonality_mode=seasonality_mode,
                changepoint_prior_scale=changepoint_prior_scale,
                seasonality_prior_scale=10.0,
                holidays_prior_scale=10.0,
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                interval_width=0.8  # 80% confidence interval
            )
            
            # Add custom seasonalities for IT infrastructure patterns
            model.add_seasonality(name='hourly', period=24, fourier_order=8)
            model.add_seasonality(name='weekly', period=7, fourier_order=4)
            
            return model
            
        except Exception as e:
            logger.error(f"❌ Error creating Prophet model: {str(e)}")
            return None
    
    def forecast_metric(self, df, node, metric, periods=24, freq='H'):
        """Forecast a specific metric for a node"""
        try:
            # Prepare data
            prophet_data = self.prepare_prophet_data(df, node, metric)
            if prophet_data is None:
                logger.warning(f"⚠️ Insufficient data for {node} {metric}")
                return None
            
            # Create and fit model
            model = self.create_prophet_model()
            if model is None:
                return None
            
            model.fit(prophet_data)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods, freq=freq)
            
            # Make forecast
            forecast = model.predict(future)
            
            # Extract forecast data
            forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
            forecast_data.columns = ['timestamp', 'forecast', 'lower_bound', 'upper_bound']
            
            # Add metadata
            forecast_data['node'] = node
            forecast_data['metric'] = metric
            forecast_data['model_type'] = 'prophet'
            forecast_data['created_at'] = datetime.now()
            
            # Calculate forecast accuracy metrics
            historical_data = prophet_data.merge(
                forecast_data[forecast_data['timestamp'].isin(prophet_data['ds'])],
                left_on='ds', right_on='timestamp', how='left'
            )
            
            if len(historical_data) > 0:
                mae = np.mean(np.abs(historical_data['y'] - historical_data['forecast']))
                mape = np.mean(np.abs((historical_data['y'] - historical_data['forecast']) / historical_data['y'])) * 100
                rmse = np.sqrt(np.mean((historical_data['y'] - historical_data['forecast']) ** 2))
                
                forecast_data['mae'] = mae
                forecast_data['mape'] = mape
                forecast_data['rmse'] = rmse
            
            logger.info(f"✅ Generated forecast for {node} {metric}")
            return forecast_data
            
        except Exception as e:
            logger.error(f"❌ Error forecasting {node} {metric}: {str(e)}")
            return None
    
    def generate_all_forecasts(self, df, periods=24, freq='H'):
        """Generate forecasts for all nodes and metrics"""
        try:
            all_forecasts = []
            nodes = df['node'].unique()
            metrics = ['cpu_utilization', 'memory_utilization', 'disk_utilization']
            
            logger.info(f"🚀 Generating forecasts for {len(nodes)} nodes and {len(metrics)} metrics...")
            
            for node in nodes:
                for metric in metrics:
                    forecast = self.forecast_metric(df, node, metric, periods, freq)
                    if forecast is not None:
                        all_forecasts.append(forecast)
            
            if all_forecasts:
                combined_forecasts = pd.concat(all_forecasts, ignore_index=True)
                logger.info(f"✅ Generated {len(combined_forecasts)} forecast records")
                return combined_forecasts
            else:
                logger.warning("⚠️ No forecasts generated")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating forecasts: {str(e)}")
            return None
    
    def create_forecast_visualizations(self, df, forecasts):
        """Create visualization plots for forecasts"""
        try:
            if forecasts is None or len(forecasts) == 0:
                logger.warning("⚠️ No forecast data to visualize")
                return
            
            nodes = forecasts['node'].unique()
            metrics = forecasts['metric'].unique()
            
            for node in nodes:
                for metric in metrics:
                    try:
                        # Filter data
                        node_forecasts = forecasts[
                            (forecasts['node'] == node) & 
                            (forecasts['metric'] == metric)
                        ].copy()
                        
                        if len(node_forecasts) == 0:
                            continue
                        
                        # Get historical data
                        historical = df[df['node'] == node][['timestamp', metric]].copy()
                        historical.columns = ['timestamp', 'value']
                        historical = historical.dropna()
                        
                        # Create plot
                        fig = go.Figure()
                        
                        # Add historical data
                        fig.add_trace(go.Scatter(
                            x=historical['timestamp'],
                            y=historical['value'],
                            mode='lines+markers',
                            name='Historical',
                            line=dict(color='blue', width=2),
                            marker=dict(size=4)
                        ))
                        
                        # Add forecast
                        fig.add_trace(go.Scatter(
                            x=node_forecasts['timestamp'],
                            y=node_forecasts['forecast'],
                            mode='lines',
                            name='Forecast',
                            line=dict(color='red', width=2, dash='dash')
                        ))
                        
                        # Add confidence interval
                        fig.add_trace(go.Scatter(
                            x=node_forecasts['timestamp'],
                            y=node_forecasts['upper_bound'],
                            mode='lines',
                            line=dict(width=0),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=node_forecasts['timestamp'],
                            y=node_forecasts['lower_bound'],
                            mode='lines',
                            line=dict(width=0),
                            fill='tonexty',
                            fillcolor='rgba(255,0,0,0.1)',
                            name='Confidence Interval',
                            hoverinfo='skip'
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{node} - {metric.replace("_", " ").title()} Forecast',
                            xaxis_title='Time',
                            yaxis_title=f'{metric.replace("_", " ").title()} (%)',
                            hovermode='x unified',
                            template='plotly_white'
                        )
                        
                        # Save plot
                        plot_path = os.path.join(
                            self.forecasts_dir, 
                            f'{node}_{metric}_forecast.html'
                        )
                        fig.write_html(plot_path)
                        
                    except Exception as e:
                        logger.error(f"❌ Error creating visualization for {node} {metric}: {str(e)}")
                        continue
            
            logger.info("✅ Created forecast visualizations")
            
        except Exception as e:
            logger.error(f"❌ Error creating visualizations: {str(e)}")
    
    def generate_capacity_recommendations(self, forecasts):
        """Generate capacity planning recommendations based on forecasts"""
        try:
            if forecasts is None or len(forecasts) == 0:
                return []
            
            recommendations = []
            current_time = datetime.now()
            
            # Get future forecasts (next 24 hours)
            future_forecasts = forecasts[forecasts['timestamp'] > current_time].copy()
            
            for node in future_forecasts['node'].unique():
                node_forecasts = future_forecasts[future_forecasts['node'] == node]
                
                for metric in node_forecasts['metric'].unique():
                    metric_forecasts = node_forecasts[node_forecasts['metric'] == metric]
                    
                    # Check for high utilization predictions
                    max_forecast = metric_forecasts['forecast'].max()
                    avg_forecast = metric_forecasts['forecast'].mean()
                    
                    if max_forecast > 90:
                        recommendations.append({
                            'node': node,
                            'metric': metric,
                            'severity': 'Critical',
                            'message': f'Predicted {metric} utilization will reach {max_forecast:.1f}% - immediate action required',
                            'recommended_action': 'Add capacity or migrate instances immediately',
                            'forecast_period': '24 hours',
                            'max_predicted_value': max_forecast
                        })
                    elif max_forecast > 80:
                        recommendations.append({
                            'node': node,
                            'metric': metric,
                            'severity': 'High',
                            'message': f'Predicted {metric} utilization will reach {max_forecast:.1f}% - plan for capacity increase',
                            'recommended_action': 'Plan capacity increase within 1-2 days',
                            'forecast_period': '24 hours',
                            'max_predicted_value': max_forecast
                        })
                    elif avg_forecast > 70:
                        recommendations.append({
                            'node': node,
                            'metric': metric,
                            'severity': 'Medium',
                            'message': f'Predicted average {metric} utilization will be {avg_forecast:.1f}% - monitor closely',
                            'recommended_action': 'Monitor trends and plan for future capacity needs',
                            'forecast_period': '24 hours',
                            'avg_predicted_value': avg_forecast
                        })
            
            logger.info(f"✅ Generated {len(recommendations)} capacity recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {str(e)}")
            return []
    
    def save_forecasts(self, forecasts, recommendations):
        """Save forecast data and recommendations"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save forecasts
            if forecasts is not None:
                forecast_file = os.path.join(self.forecasts_dir, f'forecasts_{timestamp}.csv')
                forecasts.to_csv(forecast_file, index=False)
                logger.info(f"✅ Saved forecasts to {forecast_file}")
            
            # Save recommendations
            if recommendations:
                rec_file = os.path.join(self.forecasts_dir, f'recommendations_{timestamp}.json')
                with open(rec_file, 'w') as f:
                    json.dump(recommendations, f, indent=2, default=str)
                logger.info(f"✅ Saved recommendations to {rec_file}")
            
            # Create summary report
            self.create_forecast_summary(forecasts, recommendations, timestamp)
            
        except Exception as e:
            logger.error(f"❌ Error saving forecasts: {str(e)}")
    
    def create_forecast_summary(self, forecasts, recommendations, timestamp):
        """Create a summary report of forecasts and recommendations"""
        try:
            report_path = os.path.join(self.forecasts_dir, f'forecast_summary_{timestamp}.txt')
            
            with open(report_path, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("OPENSTACK CAPACITY FORECAST REPORT\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Forecast summary
                if forecasts is not None and len(forecasts) > 0:
                    f.write("FORECAST SUMMARY\n")
                    f.write("-" * 40 + "\n")
                    
                    nodes = forecasts['node'].unique()
                    metrics = forecasts['metric'].unique()
                    
                    for node in nodes:
                        f.write(f"\nNode: {node}\n")
                        for metric in metrics:
                            node_metric_forecasts = forecasts[
                                (forecasts['node'] == node) & 
                                (forecasts['metric'] == metric)
                            ]
                            
                            if len(node_metric_forecasts) > 0:
                                max_forecast = node_metric_forecasts['forecast'].max()
                                avg_forecast = node_metric_forecasts['forecast'].mean()
                                f.write(f"  {metric.replace('_', ' ').title()}: Max {max_forecast:.1f}%, Avg {avg_forecast:.1f}%\n")
                
                # Recommendations
                if recommendations:
                    f.write("\nCAPACITY RECOMMENDATIONS\n")
                    f.write("-" * 40 + "\n")
                    
                    critical_recs = [r for r in recommendations if r['severity'] == 'Critical']
                    high_recs = [r for r in recommendations if r['severity'] == 'High']
                    medium_recs = [r for r in recommendations if r['severity'] == 'Medium']
                    
                    if critical_recs:
                        f.write("\n🚨 CRITICAL ALERTS:\n")
                        for rec in critical_recs:
                            f.write(f"  • {rec['node']} - {rec['message']}\n")
                            f.write(f"    Action: {rec['recommended_action']}\n\n")
                    
                    if high_recs:
                        f.write("\n⚠️ HIGH PRIORITY:\n")
                        for rec in high_recs:
                            f.write(f"  • {rec['node']} - {rec['message']}\n")
                            f.write(f"    Action: {rec['recommended_action']}\n\n")
                    
                    if medium_recs:
                        f.write("\n📊 MEDIUM PRIORITY:\n")
                        for rec in medium_recs:
                            f.write(f"  • {rec['node']} - {rec['message']}\n")
                            f.write(f"    Action: {rec['recommended_action']}\n\n")
                else:
                    f.write("\n✅ No immediate capacity concerns detected\n")
            
            logger.info("✅ Created forecast summary report")
            
        except Exception as e:
            logger.error(f"❌ Error creating forecast summary: {str(e)}")
    
    def run_forecasting(self, periods=24, freq='H'):
        """Run complete forecasting analysis"""
        logger.info("🚀 Starting OpenStack usage forecasting...")
        
        # Load data
        df = self.load_metrics()
        if df is None:
            return False
        
        # Generate forecasts
        forecasts = self.generate_all_forecasts(df, periods, freq)
        if forecasts is None:
            logger.warning("⚠️ No forecasts generated")
            return False
        
        # Create visualizations
        self.create_forecast_visualizations(df, forecasts)
        
        # Generate recommendations
        recommendations = self.generate_capacity_recommendations(forecasts)
        
        # Save results
        self.save_forecasts(forecasts, recommendations)
        
        logger.info("✅ Forecasting completed successfully")
        return True

def main():
    """Main entry point"""
    forecaster = UsageForecaster()
    success = forecaster.run_forecasting()
    
    if success:
        print("✅ OpenStack usage forecasting completed successfully!")
    else:
        print("❌ OpenStack usage forecasting failed!")
        exit(1)

if __name__ == "__main__":
    main()
