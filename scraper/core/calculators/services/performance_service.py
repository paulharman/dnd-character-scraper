"""
Performance Service

Comprehensive performance monitoring and metrics collection service for the calculator system.
This service provides detailed performance tracking, alerting, reporting, and optimization insights.
"""

from typing import Dict, Any, List, Optional, Callable, Union
import logging
import time
import psutil
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from statistics import mean, median, stdev
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    timestamp: datetime
    unit: str = "ms"
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Performance report with statistics and analysis."""
    service_name: str
    start_time: datetime
    end_time: datetime
    total_duration: float
    metrics: List[PerformanceMetric] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceThreshold:
    """Performance threshold for alerting."""
    metric_name: str
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    max_avg_value: Optional[float] = None
    alert_message: str = ""
    severity: str = "warning"  # info, warning, error, critical


class PerformanceCollector:
    """Collects and stores performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        """
        Initialize the performance collector.
        
        Args:
            max_metrics: Maximum number of metrics to store
        """
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self.lock:
            self.metrics.append(metric)
    
    def get_metrics(self, metric_name: str = None, 
                   since: datetime = None,
                   until: datetime = None) -> List[PerformanceMetric]:
        """
        Get metrics with optional filtering.
        
        Args:
            metric_name: Filter by metric name
            since: Filter metrics after this time
            until: Filter metrics before this time
            
        Returns:
            List of filtered metrics
        """
        with self.lock:
            filtered_metrics = list(self.metrics)
        
        if metric_name:
            filtered_metrics = [m for m in filtered_metrics if m.name == metric_name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        if until:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= until]
        
        return filtered_metrics
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        with self.lock:
            self.metrics.clear()
    
    def get_metric_count(self) -> int:
        """Get the total number of stored metrics."""
        with self.lock:
            return len(self.metrics)


class PerformanceAnalyzer:
    """Analyzes performance metrics and generates insights."""
    
    def __init__(self):
        """Initialize the performance analyzer."""
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
    
    def analyze_metrics(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """
        Analyze a list of performance metrics.
        
        Args:
            metrics: List of metrics to analyze
            
        Returns:
            Analysis results
        """
        if not metrics:
            return {}
        
        # Group metrics by name
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.name].append(metric.value)
        
        analysis = {}
        for metric_name, values in grouped_metrics.items():
            if len(values) == 1:
                stats = {
                    'count': 1,
                    'min': values[0],
                    'max': values[0],
                    'mean': values[0],
                    'median': values[0],
                    'std_dev': 0.0
                }
            else:
                stats = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': mean(values),
                    'median': median(values),
                    'std_dev': stdev(values) if len(values) > 1 else 0.0
                }
            
            # Calculate percentiles
            sorted_values = sorted(values)
            count = len(sorted_values)
            stats['p50'] = sorted_values[int(count * 0.5)]
            stats['p90'] = sorted_values[int(count * 0.9)]
            stats['p95'] = sorted_values[int(count * 0.95)]
            stats['p99'] = sorted_values[int(count * 0.99)]
            
            analysis[metric_name] = stats
        
        return analysis
    
    def compare_with_baseline(self, metrics: List[PerformanceMetric], 
                            metric_name: str) -> Dict[str, Any]:
        """
        Compare metrics with baseline.
        
        Args:
            metrics: Current metrics
            metric_name: Name of metric to compare
            
        Returns:
            Comparison results
        """
        if metric_name not in self.baseline_metrics:
            return {'error': f'No baseline found for metric: {metric_name}'}
        
        current_values = [m.value for m in metrics if m.name == metric_name]
        if not current_values:
            return {'error': f'No current metrics found for: {metric_name}'}
        
        baseline = self.baseline_metrics[metric_name]
        current_mean = mean(current_values)
        
        comparison = {
            'baseline_mean': baseline['mean'],
            'current_mean': current_mean,
            'difference': current_mean - baseline['mean'],
            'percentage_change': ((current_mean - baseline['mean']) / baseline['mean']) * 100
        }
        
        return comparison
    
    def set_baseline(self, metrics: List[PerformanceMetric]):
        """
        Set baseline metrics for comparison.
        
        Args:
            metrics: Metrics to use as baseline
        """
        analysis = self.analyze_metrics(metrics)
        self.baseline_metrics = analysis
    
    def detect_anomalies(self, metrics: List[PerformanceMetric], 
                        threshold_multiplier: float = 2.0) -> List[PerformanceMetric]:
        """
        Detect anomalous metrics using statistical methods.
        
        Args:
            metrics: Metrics to analyze
            threshold_multiplier: Multiplier for standard deviation threshold
            
        Returns:
            List of anomalous metrics
        """
        if len(metrics) < 10:  # Need sufficient data for anomaly detection
            return []
        
        # Group by metric name
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.name].append(metric)
        
        anomalies = []
        
        for metric_name, metric_list in grouped_metrics.items():
            values = [m.value for m in metric_list]
            
            if len(values) < 10:
                continue
            
            metric_mean = mean(values)
            metric_std = stdev(values)
            threshold = metric_std * threshold_multiplier
            
            for metric in metric_list:
                if abs(metric.value - metric_mean) > threshold:
                    anomalies.append(metric)
        
        return anomalies


class PerformanceService:
    """
    Comprehensive performance monitoring service.
    
    This service provides:
    - Real-time performance metric collection
    - Statistical analysis and reporting
    - Threshold-based alerting
    - Performance baseline management
    - System resource monitoring
    - Export and persistence capabilities
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the performance service.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Core components
        self.collector = PerformanceCollector()
        self.analyzer = PerformanceAnalyzer()
        
        # Thresholds and alerting
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: List[str] = []
        
        # System monitoring
        self.system_monitoring_enabled = True
        self.system_metrics_interval = 60  # seconds
        self.last_system_check = datetime.now()
        
        # Active measurements
        self.active_measurements: Dict[str, datetime] = {}
        
        # Configuration
        self.config = {
            'max_metrics': 10000,
            'auto_baseline_updates': True,
            'anomaly_detection_enabled': True,
            'system_monitoring_enabled': True
        }
        
        # Initialize default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds."""
        default_thresholds = [
            PerformanceThreshold(
                metric_name="calculation_time",
                max_value=5000.0,  # 5 seconds
                alert_message="Calculation taking longer than 5 seconds",
                severity="warning"
            ),
            PerformanceThreshold(
                metric_name="coordinator_time",
                max_value=1000.0,  # 1 second
                alert_message="Coordinator execution taking longer than 1 second",
                severity="warning"
            ),
            PerformanceThreshold(
                metric_name="memory_usage_mb",
                max_value=1000.0,  # 1GB
                alert_message="Memory usage exceeding 1GB",
                severity="error"
            )
        ]
        
        for threshold in default_thresholds:
            self.add_threshold(threshold)
    
    def start_measurement(self, measurement_name: str, tags: Dict[str, str] = None) -> str:
        """
        Start a performance measurement.
        
        Args:
            measurement_name: Name of the measurement
            tags: Optional tags for the measurement
            
        Returns:
            Measurement ID for stopping the measurement
        """
        measurement_id = f"{measurement_name}_{int(time.time() * 1000)}"
        self.active_measurements[measurement_id] = datetime.now()
        
        self.logger.debug(f"Started measurement: {measurement_name} (ID: {measurement_id})")
        return measurement_id
    
    def stop_measurement(self, measurement_id: str, 
                        tags: Dict[str, str] = None,
                        metadata: Dict[str, Any] = None) -> PerformanceMetric:
        """
        Stop a performance measurement and record the metric.
        
        Args:
            measurement_id: ID returned by start_measurement
            tags: Optional tags for the metric
            metadata: Optional metadata for the metric
            
        Returns:
            The recorded performance metric
        """
        if measurement_id not in self.active_measurements:
            raise ValueError(f"No active measurement found with ID: {measurement_id}")
        
        start_time = self.active_measurements[measurement_id]
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        
        # Extract measurement name from ID
        measurement_name = measurement_id.rsplit('_', 1)[0]
        
        metric = PerformanceMetric(
            name=measurement_name,
            value=duration,
            timestamp=end_time,
            unit="ms",
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.record_metric(metric)
        del self.active_measurements[measurement_id]
        
        self.logger.debug(f"Stopped measurement: {measurement_name} ({duration:.2f}ms)")
        return metric
    
    def record_metric(self, metric: PerformanceMetric):
        """
        Record a performance metric.
        
        Args:
            metric: The metric to record
        """
        self.collector.record_metric(metric)
        
        # Check thresholds
        self._check_thresholds(metric)
        
        # Update baseline if auto-updates are enabled
        if self.config.get('auto_baseline_updates', True):
            self._update_baseline_if_needed(metric)
    
    def record_value(self, metric_name: str, value: float, 
                    unit: str = "ms", tags: Dict[str, str] = None,
                    metadata: Dict[str, Any] = None):
        """
        Record a metric value directly.
        
        Args:
            metric_name: Name of the metric
            value: Value to record
            unit: Unit of measurement
            tags: Optional tags
            metadata: Optional metadata
        """
        metric = PerformanceMetric(
            name=metric_name,
            value=value,
            timestamp=datetime.now(),
            unit=unit,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.record_metric(metric)
    
    def add_threshold(self, threshold: PerformanceThreshold):
        """
        Add a performance threshold.
        
        Args:
            threshold: Threshold to add
        """
        self.thresholds[threshold.metric_name] = threshold
        self.logger.info(f"Added threshold for metric: {threshold.metric_name}")
    
    def remove_threshold(self, metric_name: str):
        """
        Remove a performance threshold.
        
        Args:
            metric_name: Name of the metric threshold to remove
        """
        if metric_name in self.thresholds:
            del self.thresholds[metric_name]
            self.logger.info(f"Removed threshold for metric: {metric_name}")
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if a metric violates any thresholds."""
        threshold = self.thresholds.get(metric.name)
        if not threshold:
            return
        
        violated = False
        alert_parts = []
        
        if threshold.max_value is not None and metric.value > threshold.max_value:
            violated = True
            alert_parts.append(f"value {metric.value} > max {threshold.max_value}")
        
        if threshold.min_value is not None and metric.value < threshold.min_value:
            violated = True
            alert_parts.append(f"value {metric.value} < min {threshold.min_value}")
        
        if violated:
            alert_message = threshold.alert_message or f"Threshold violated for {metric.name}"
            full_alert = f"[{threshold.severity.upper()}] {alert_message} ({', '.join(alert_parts)})"
            self.alerts.append(full_alert)
            
            if threshold.severity in ['error', 'critical']:
                self.logger.error(full_alert)
            else:
                self.logger.warning(full_alert)
    
    def _update_baseline_if_needed(self, metric: PerformanceMetric):
        """Update baseline metrics if conditions are met."""
        # Simple auto-baseline update: every 1000 metrics of the same type
        metrics = self.collector.get_metrics(metric.name)
        if len(metrics) % 1000 == 0 and len(metrics) > 0:
            self.analyzer.set_baseline(metrics[-1000:])  # Use last 1000 metrics
            self.logger.info(f"Updated baseline for metric: {metric.name}")
    
    def get_performance_report(self, metric_name: str = None,
                             since: datetime = None,
                             until: datetime = None) -> PerformanceReport:
        """
        Generate a performance report.
        
        Args:
            metric_name: Filter by metric name
            since: Include metrics since this time
            until: Include metrics until this time
            
        Returns:
            Performance report
        """
        metrics = self.collector.get_metrics(metric_name, since, until)
        
        if not metrics:
            return PerformanceReport(
                service_name="performance_service",
                start_time=datetime.now(),
                end_time=datetime.now(),
                total_duration=0.0
            )
        
        start_time = min(m.timestamp for m in metrics)
        end_time = max(m.timestamp for m in metrics)
        total_duration = (end_time - start_time).total_seconds()
        
        # Analyze metrics
        statistics = self.analyzer.analyze_metrics(metrics)
        
        # Detect anomalies if enabled
        anomalies = []
        if self.config.get('anomaly_detection_enabled', True):
            anomalies = self.analyzer.detect_anomalies(metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(statistics, anomalies)
        
        report = PerformanceReport(
            service_name="performance_service",
            start_time=start_time,
            end_time=end_time,
            total_duration=total_duration,
            metrics=metrics,
            statistics=statistics,
            alerts=self.alerts.copy(),
            recommendations=recommendations
        )
        
        return report
    
    def _generate_recommendations(self, statistics: Dict[str, Any], 
                                anomalies: List[PerformanceMetric]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        for metric_name, stats in statistics.items():
            # High variance recommendations
            if stats.get('std_dev', 0) > stats.get('mean', 0) * 0.5:
                recommendations.append(
                    f"High variance detected in {metric_name}. Consider investigating consistency issues."
                )
            
            # High P99 recommendations
            p99 = stats.get('p99', 0)
            mean_val = stats.get('mean', 0)
            if p99 > mean_val * 3:
                recommendations.append(
                    f"P99 latency for {metric_name} is significantly higher than average. "
                    f"Consider optimizing worst-case scenarios."
                )
        
        # Anomaly recommendations
        if anomalies:
            recommendations.append(
                f"Detected {len(anomalies)} anomalous metrics. "
                f"Review system load and resource usage during these periods."
            )
        
        return recommendations
    
    def monitor_system_resources(self):
        """Monitor system resource usage."""
        if not self.system_monitoring_enabled:
            return
        
        now = datetime.now()
        if (now - self.last_system_check).seconds < self.system_metrics_interval:
            return
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_value("system_cpu_percent", cpu_percent, "percent")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_value("system_memory_percent", memory.percent, "percent")
            self.record_value("system_memory_used_mb", memory.used / 1024 / 1024, "MB")
            
            # Disk usage for current directory
            disk = psutil.disk_usage('.')
            disk_percent = (disk.used / disk.total) * 100
            self.record_value("system_disk_percent", disk_percent, "percent")
            
            self.last_system_check = now
            
        except Exception as e:
            self.logger.error(f"Error monitoring system resources: {e}")
    
    def export_metrics(self, file_path: str, format: str = "json",
                      metric_name: str = None, since: datetime = None):
        """
        Export metrics to a file.
        
        Args:
            file_path: Path to export file
            format: Export format (json, csv)
            metric_name: Filter by metric name
            since: Export metrics since this time
        """
        metrics = self.collector.get_metrics(metric_name, since)
        
        if format.lower() == "json":
            export_data = []
            for metric in metrics:
                export_data.append({
                    'name': metric.name,
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'unit': metric.unit,
                    'tags': metric.tags,
                    'metadata': metric.metadata
                })
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'value', 'timestamp', 'unit'])
                
                for metric in metrics:
                    writer.writerow([
                        metric.name,
                        metric.value,
                        metric.timestamp.isoformat(),
                        metric.unit
                    ])
        
        self.logger.info(f"Exported {len(metrics)} metrics to {file_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'total_metrics': self.collector.get_metric_count(),
            'active_measurements': len(self.active_measurements),
            'threshold_count': len(self.thresholds),
            'alert_count': len(self.alerts),
            'system_monitoring_enabled': self.system_monitoring_enabled,
            'last_system_check': self.last_system_check.isoformat()
        }
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        self.collector.clear_metrics()
        self.alerts.clear()
        self.logger.info("Cleared all performance metrics and alerts")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the performance service."""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'active_measurements': list(self.active_measurements.keys()),
            'recent_alerts': self.alerts[-10:] if self.alerts else []
        }