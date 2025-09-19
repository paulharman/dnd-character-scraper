"""
Performance monitoring utilities for the calculator system.

This module provides performance monitoring, profiling, and optimization
tools for the character calculation pipeline.
"""

import time
import logging
import functools
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime
# Removed psutil dependency - performance monitoring is optional
PSUTIL_AVAILABLE = False
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a calculation operation."""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    operation_name: str
    call_count: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    success_count: int
    error_count: int
    avg_memory_usage: float
    avg_cpu_usage: float
    last_execution: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.call_count == 0:
            return 0.0
        return (self.success_count / self.call_count) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
        if self.call_count == 0:
            return 0.0
        return (self.error_count / self.call_count) * 100


class PerformanceMonitor:
    """
    Monitor and track performance metrics for calculation operations.
    
    Provides decorators and context managers for measuring execution time,
    memory usage, and other performance metrics.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the performance monitor.
        
        Args:
            max_history: Maximum number of metrics to keep in history
        """
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.aggregated_stats: Dict[str, PerformanceStats] = {}
        self.lock = threading.Lock()
        self.enabled = True
        
    def enable(self) -> None:
        """Enable performance monitoring."""
        self.enabled = True
        
    def disable(self) -> None:
        """Disable performance monitoring."""
        self.enabled = False
        
    def monitor(self, operation_name: str = None, 
                include_memory: bool = True,
                include_cpu: bool = True):
        """
        Decorator to monitor function performance.
        
        Args:
            operation_name: Name of the operation (defaults to function name)
            include_memory: Whether to monitor memory usage
            include_cpu: Whether to monitor CPU usage
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                with self.measure_operation(op_name, include_memory, include_cpu):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @contextmanager
    def measure_operation(self, operation_name: str,
                         include_memory: bool = True,
                         include_cpu: bool = True):
        """
        Context manager to measure operation performance.
        
        Args:
            operation_name: Name of the operation
            include_memory: Whether to monitor memory usage
            include_cpu: Whether to monitor CPU usage
            
        Yields:
            PerformanceMetrics object (populated after operation)
        """
        if not self.enabled:
            yield None
            return
            
        start_time = time.time()
        start_memory = self._get_memory_usage() if include_memory else 0.0
        start_cpu = self._get_cpu_usage() if include_cpu else 0.0
        
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0.0,
            duration=0.0,
            memory_usage=0.0,
            cpu_usage=0.0,
            success=True
        )
        
        try:
            yield metrics
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            logger.error(f"Performance monitoring caught error in {operation_name}: {e}")
            raise
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage() if include_memory else 0.0
            end_cpu = self._get_cpu_usage() if include_cpu else 0.0
            
            metrics.end_time = end_time
            metrics.duration = end_time - start_time
            metrics.memory_usage = end_memory - start_memory
            metrics.cpu_usage = end_cpu - start_cpu
            
            self._record_metrics(metrics)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)  # MB
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        if not PSUTIL_AVAILABLE:
            return 0.0
        try:
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0
    
    def _record_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics in history."""
        with self.lock:
            self.metrics_history[metrics.operation_name].append(metrics)
            self._update_aggregated_stats(metrics)
    
    def _update_aggregated_stats(self, metrics: PerformanceMetrics) -> None:
        """Update aggregated statistics with new metrics."""
        operation_name = metrics.operation_name
        
        if operation_name not in self.aggregated_stats:
            self.aggregated_stats[operation_name] = PerformanceStats(
                operation_name=operation_name,
                call_count=0,
                total_duration=0.0,
                avg_duration=0.0,
                min_duration=float('inf'),
                max_duration=0.0,
                success_count=0,
                error_count=0,
                avg_memory_usage=0.0,
                avg_cpu_usage=0.0,
                last_execution=None
            )
        
        stats = self.aggregated_stats[operation_name]
        stats.call_count += 1
        stats.total_duration += metrics.duration
        stats.avg_duration = stats.total_duration / stats.call_count
        stats.min_duration = min(stats.min_duration, metrics.duration)
        stats.max_duration = max(stats.max_duration, metrics.duration)
        stats.last_execution = datetime.now()
        
        if metrics.success:
            stats.success_count += 1
        else:
            stats.error_count += 1
        
        # Update average memory and CPU usage
        stats.avg_memory_usage = (
            (stats.avg_memory_usage * (stats.call_count - 1) + metrics.memory_usage) / stats.call_count
        )
        stats.avg_cpu_usage = (
            (stats.avg_cpu_usage * (stats.call_count - 1) + metrics.cpu_usage) / stats.call_count
        )
    
    def get_metrics(self, operation_name: str) -> List[PerformanceMetrics]:
        """
        Get all metrics for a specific operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            List of performance metrics
        """
        with self.lock:
            return list(self.metrics_history.get(operation_name, []))
    
    def get_stats(self, operation_name: str) -> Optional[PerformanceStats]:
        """
        Get aggregated statistics for a specific operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Performance statistics or None if not found
        """
        with self.lock:
            return self.aggregated_stats.get(operation_name)
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """
        Get aggregated statistics for all operations.
        
        Returns:
            Dictionary of operation names to performance statistics
        """
        with self.lock:
            return self.aggregated_stats.copy()
    
    def get_slow_operations(self, threshold_ms: float = 1000.0) -> List[PerformanceStats]:
        """
        Get operations that exceed the performance threshold.
        
        Args:
            threshold_ms: Threshold in milliseconds
            
        Returns:
            List of slow operations
        """
        threshold_s = threshold_ms / 1000.0
        with self.lock:
            return [
                stats for stats in self.aggregated_stats.values()
                if stats.avg_duration > threshold_s
            ]
    
    def get_error_prone_operations(self, error_rate_threshold: float = 5.0) -> List[PerformanceStats]:
        """
        Get operations with high error rates.
        
        Args:
            error_rate_threshold: Error rate threshold as percentage
            
        Returns:
            List of error-prone operations
        """
        with self.lock:
            return [
                stats for stats in self.aggregated_stats.values()
                if stats.error_rate > error_rate_threshold
            ]
    
    def reset_stats(self, operation_name: str = None) -> None:
        """
        Reset statistics for a specific operation or all operations.
        
        Args:
            operation_name: Operation to reset (None for all)
        """
        with self.lock:
            if operation_name:
                self.metrics_history.pop(operation_name, None)
                self.aggregated_stats.pop(operation_name, None)
            else:
                self.metrics_history.clear()
                self.aggregated_stats.clear()
    
    def generate_report(self, top_n: int = 10) -> str:
        """
        Generate a performance report.
        
        Args:
            top_n: Number of top operations to include
            
        Returns:
            Formatted performance report
        """
        with self.lock:
            stats_list = sorted(
                self.aggregated_stats.values(),
                key=lambda s: s.avg_duration,
                reverse=True
            )[:top_n]
            
            report = ["Performance Report", "=" * 50]
            
            for stats in stats_list:
                report.append(f"Operation: {stats.operation_name}")
                report.append(f"  Calls: {stats.call_count}")
                report.append(f"  Avg Duration: {stats.avg_duration:.3f}s ({stats.avg_duration * 1000:.1f}ms)")
                report.append(f"  Min/Max Duration: {stats.min_duration:.3f}s / {stats.max_duration:.3f}s")
                report.append(f"  Success Rate: {stats.success_rate:.1f}%")
                report.append(f"  Avg Memory: {stats.avg_memory_usage:.1f}MB")
                report.append(f"  Avg CPU: {stats.avg_cpu_usage:.1f}%")
                report.append("")
            
            return "\n".join(report)


class PerformanceProfiler:
    """
    Advanced profiling capabilities for detailed performance analysis.
    
    Provides line-by-line profiling, call stack analysis, and
    performance bottleneck identification.
    """
    
    def __init__(self):
        """Initialize the profiler."""
        self.profiles: Dict[str, Any] = {}
        self.active_profiles: Dict[str, Any] = {}
        self.lock = threading.Lock()
    
    def profile(self, operation_name: str, 
                profile_type: str = "cProfile",
                sort_by: str = "cumulative"):
        """
        Decorator to profile function execution.
        
        Args:
            operation_name: Name of the operation
            profile_type: Type of profiling ('cProfile' or 'line_profiler')
            sort_by: Sort criteria for results
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if profile_type == "cProfile":
                    return self._profile_with_cprofile(func, operation_name, sort_by, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _profile_with_cprofile(self, func: Callable, operation_name: str, 
                              sort_by: str, *args, **kwargs):
        """Profile function with cProfile."""
        import cProfile
        import pstats
        import io
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
            
            # Capture profiling results
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats(sort_by)
            stats.print_stats()
            
            with self.lock:
                self.profiles[operation_name] = {
                    'type': 'cProfile',
                    'timestamp': datetime.now(),
                    'stats': stats,
                    'report': stream.getvalue()
                }
        
        return result
    
    def get_profile(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """
        Get profiling results for an operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Profiling results or None if not found
        """
        with self.lock:
            return self.profiles.get(operation_name)
    
    def get_profile_report(self, operation_name: str) -> Optional[str]:
        """
        Get formatted profiling report for an operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Formatted profiling report or None if not found
        """
        profile = self.get_profile(operation_name)
        if profile:
            return profile.get('report')
        return None
    
    def clear_profiles(self) -> None:
        """Clear all profiling data."""
        with self.lock:
            self.profiles.clear()
            self.active_profiles.clear()


class PerformanceOptimizer:
    """
    Performance optimization suggestions and automatic optimizations.
    
    Analyzes performance data to identify bottlenecks and suggests
    or applies optimizations.
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        """
        Initialize the optimizer.
        
        Args:
            monitor: Performance monitor instance
        """
        self.monitor = monitor
        self.optimization_rules = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Set up default optimization rules."""
        self.optimization_rules = [
            {
                'name': 'slow_calculation',
                'condition': lambda stats: stats.avg_duration > 1.0,
                'suggestion': 'Consider caching results or optimizing algorithm'
            },
            {
                'name': 'high_memory_usage',
                'condition': lambda stats: stats.avg_memory_usage > 100.0,
                'suggestion': 'Consider memory optimization or batch processing'
            },
            {
                'name': 'high_error_rate',
                'condition': lambda stats: stats.error_rate > 10.0,
                'suggestion': 'Review error handling and input validation'
            },
            {
                'name': 'frequent_calls',
                'condition': lambda stats: stats.call_count > 1000,
                'suggestion': 'Consider caching if results are deterministic'
            }
        ]
    
    def analyze_performance(self) -> Dict[str, List[str]]:
        """
        Analyze current performance and generate optimization suggestions.
        
        Returns:
            Dictionary of operation names to optimization suggestions
        """
        suggestions = {}
        all_stats = self.monitor.get_all_stats()
        
        for operation_name, stats in all_stats.items():
            operation_suggestions = []
            
            for rule in self.optimization_rules:
                if rule['condition'](stats):
                    operation_suggestions.append(rule['suggestion'])
            
            if operation_suggestions:
                suggestions[operation_name] = operation_suggestions
        
        return suggestions
    
    def get_optimization_report(self) -> str:
        """
        Generate a comprehensive optimization report.
        
        Returns:
            Formatted optimization report
        """
        suggestions = self.analyze_performance()
        
        if not suggestions:
            return "No optimization suggestions at this time."
        
        report = ["Performance Optimization Report", "=" * 40]
        
        for operation_name, operation_suggestions in suggestions.items():
            stats = self.monitor.get_stats(operation_name)
            
            report.append(f"\nOperation: {operation_name}")
            report.append(f"Current Performance:")
            report.append(f"  Average Duration: {stats.avg_duration:.3f}s")
            report.append(f"  Average Memory: {stats.avg_memory_usage:.1f}MB")
            report.append(f"  Error Rate: {stats.error_rate:.1f}%")
            report.append(f"  Call Count: {stats.call_count}")
            
            report.append("Suggestions:")
            for suggestion in operation_suggestions:
                report.append(f"  - {suggestion}")
        
        return "\n".join(report)


# Global performance monitor instance
global_monitor = PerformanceMonitor()
global_profiler = PerformanceProfiler()
global_optimizer = PerformanceOptimizer(global_monitor)


def monitor_performance(operation_name: str = None, 
                       include_memory: bool = True,
                       include_cpu: bool = True):
    """
    Convenience decorator for monitoring performance.
    
    Args:
        operation_name: Name of the operation
        include_memory: Whether to monitor memory usage
        include_cpu: Whether to monitor CPU usage
        
    Returns:
        Decorated function
    """
    return global_monitor.monitor(operation_name, include_memory, include_cpu)


def profile_performance(operation_name: str = None,
                       profile_type: str = "cProfile",
                       sort_by: str = "cumulative"):
    """
    Convenience decorator for profiling performance.
    
    Args:
        operation_name: Name of the operation
        profile_type: Type of profiling
        sort_by: Sort criteria for results
        
    Returns:
        Decorated function
    """
    return global_profiler.profile(operation_name, profile_type, sort_by)


def get_performance_report(top_n: int = 10) -> str:
    """
    Get a performance report from the global monitor.
    
    Args:
        top_n: Number of top operations to include
        
    Returns:
        Formatted performance report
    """
    return global_monitor.generate_report(top_n)


def get_optimization_report() -> str:
    """
    Get an optimization report from the global optimizer.
    
    Returns:
        Formatted optimization report
    """
    return global_optimizer.get_optimization_report()


def reset_performance_data() -> None:
    """Reset all performance monitoring data."""
    global_monitor.reset_stats()
    global_profiler.clear_profiles()