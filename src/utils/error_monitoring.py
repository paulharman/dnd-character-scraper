"""
Error Monitoring Utilities

Provides utilities for monitoring, analyzing, and reporting on error patterns
in the enhanced Discord change tracking system.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

from src.services.error_handler import ErrorHandler, ErrorRecord, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class ErrorMonitor:
    """
    Monitor and analyze error patterns for system health insights.
    """
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_health_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive system health report."""
        try:
            stats = self.error_handler.get_error_statistics(hours=hours)
            component_health = self.error_handler.get_component_health_status()
            
            # Calculate health score (0-100)
            health_score = self._calculate_health_score(stats, component_health)
            
            # Identify critical issues
            critical_issues = self._identify_critical_issues(stats, component_health)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(stats, component_health)
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'time_period_hours': hours,
                'overall_health_score': health_score,
                'system_status': self._determine_system_status(health_score),
                'error_statistics': stats,
                'component_health': component_health,
                'critical_issues': critical_issues,
                'recommendations': recommendations,
                'trending': self._analyze_error_trends(hours)
            }
            
            self.logger.info(f"Generated health report: {health_score}/100 health score")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}", exc_info=True)
            return {'error': str(e), 'report_timestamp': datetime.now().isoformat()}
    
    def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """Check for conditions that should trigger alerts."""
        alerts = []
        
        try:
            # Check error rate in last hour
            recent_stats = self.error_handler.get_error_statistics(hours=1)
            
            if recent_stats.get('total_errors', 0) > 10:
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'message': f"High error rate: {recent_stats['total_errors']} errors in last hour",
                    'details': recent_stats
                })
            
            # Check for critical errors
            critical_errors = recent_stats.get('errors_by_severity', {}).get('critical', 0)
            if critical_errors > 0:
                alerts.append({
                    'type': 'critical_errors',
                    'severity': 'critical',
                    'message': f"Critical errors detected: {critical_errors} in last hour",
                    'details': {'critical_error_count': critical_errors}
                })
            
            # Check component health
            component_health = self.error_handler.get_component_health_status()
            failing_components = [
                name for name, status in component_health.items() 
                if not status['healthy'] and status.get('consecutive_failures', 0) >= 3
            ]
            
            if failing_components:
                alerts.append({
                    'type': 'component_failures',
                    'severity': 'medium',
                    'message': f"Components with repeated failures: {', '.join(failing_components)}",
                    'details': {'failing_components': failing_components}
                })
            
            # Check resolution rate
            resolution_rate = recent_stats.get('resolution_rate_percent', 100)
            if resolution_rate < 50:
                alerts.append({
                    'type': 'low_resolution_rate',
                    'severity': 'medium',
                    'message': f"Low error resolution rate: {resolution_rate}%",
                    'details': {'resolution_rate': resolution_rate}
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}", exc_info=True)
            return [{'type': 'monitoring_error', 'severity': 'high', 'message': str(e)}]
    
    def analyze_error_patterns(self, days: int = 7) -> Dict[str, Any]:
        """Analyze error patterns over time to identify trends."""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            recent_errors = [
                e for e in self.error_handler.error_records 
                if e.timestamp >= cutoff_time
            ]
            
            # Group errors by day
            daily_counts = {}
            for error in recent_errors:
                day_key = error.timestamp.date().isoformat()
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            # Analyze by component
            component_patterns = {}
            for error in recent_errors:
                component = error.component
                if component not in component_patterns:
                    component_patterns[component] = {
                        'total_errors': 0,
                        'error_types': {},
                        'severity_distribution': {},
                        'resolution_rate': 0,
                        'avg_retry_count': 0
                    }
                
                pattern = component_patterns[component]
                pattern['total_errors'] += 1
                pattern['error_types'][error.exception_type] = pattern['error_types'].get(error.exception_type, 0) + 1
                pattern['severity_distribution'][error.severity.value] = pattern['severity_distribution'].get(error.severity.value, 0) + 1
                
                if error.resolved:
                    pattern['resolution_rate'] += 1
                
                pattern['avg_retry_count'] += error.retry_count
            
            # Calculate averages and rates
            for component, pattern in component_patterns.items():
                if pattern['total_errors'] > 0:
                    pattern['resolution_rate'] = (pattern['resolution_rate'] / pattern['total_errors']) * 100
                    pattern['avg_retry_count'] = pattern['avg_retry_count'] / pattern['total_errors']
            
            # Identify trending issues
            trending_issues = self._identify_trending_issues(recent_errors)
            
            return {
                'analysis_period_days': days,
                'total_errors_analyzed': len(recent_errors),
                'daily_error_counts': daily_counts,
                'component_patterns': component_patterns,
                'trending_issues': trending_issues,
                'most_problematic_components': self._rank_problematic_components(component_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing error patterns: {e}", exc_info=True)
            return {'error': str(e)}
    
    def export_error_report(self, output_path: Path, hours: int = 24) -> bool:
        """Export comprehensive error report to file."""
        try:
            report = {
                'health_report': self.generate_health_report(hours),
                'error_patterns': self.analyze_error_patterns(days=max(1, hours // 24)),
                'alert_conditions': self.check_alert_conditions(),
                'raw_error_records': [
                    error.to_dict() for error in self.error_handler.error_records[-100:]  # Last 100 errors
                ]
            }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Exported error report to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting error report: {e}", exc_info=True)
            return False
    
    def _calculate_health_score(self, stats: Dict[str, Any], component_health: Dict[str, Any]) -> int:
        """Calculate overall system health score (0-100)."""
        try:
            score = 100
            
            # Deduct points for errors
            total_errors = stats.get('total_errors', 0)
            if total_errors > 0:
                # Deduct more points for higher error counts
                error_penalty = min(50, total_errors * 2)  # Max 50 points for errors
                score -= error_penalty
            
            # Deduct points for low resolution rate
            resolution_rate = stats.get('resolution_rate_percent', 100)
            if resolution_rate < 100:
                resolution_penalty = (100 - resolution_rate) * 0.3  # Max 30 points
                score -= resolution_penalty
            
            # Deduct points for unhealthy components
            total_components = len(component_health)
            if total_components > 0:
                unhealthy_components = len([
                    c for c in component_health.values() if not c['healthy']
                ])
                component_penalty = (unhealthy_components / total_components) * 20  # Max 20 points
                score -= component_penalty
            
            # Deduct extra points for critical errors
            critical_errors = stats.get('errors_by_severity', {}).get('critical', 0)
            if critical_errors > 0:
                score -= critical_errors * 10  # 10 points per critical error
            
            return max(0, int(score))
            
        except Exception as e:
            self.logger.error(f"Error calculating health score: {e}")
            return 50  # Default to middle score on error
    
    def _determine_system_status(self, health_score: int) -> str:
        """Determine system status based on health score."""
        if health_score >= 90:
            return "excellent"
        elif health_score >= 75:
            return "good"
        elif health_score >= 50:
            return "fair"
        elif health_score >= 25:
            return "poor"
        else:
            return "critical"
    
    def _identify_critical_issues(self, stats: Dict[str, Any], component_health: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical issues requiring immediate attention."""
        issues = []
        
        # Critical errors
        critical_errors = stats.get('errors_by_severity', {}).get('critical', 0)
        if critical_errors > 0:
            issues.append({
                'type': 'critical_errors',
                'severity': 'critical',
                'description': f"{critical_errors} critical errors detected",
                'impact': 'System functionality may be severely impacted'
            })
        
        # High error rate
        total_errors = stats.get('total_errors', 0)
        time_period = stats.get('time_period_hours', 24)
        error_rate = total_errors / time_period if time_period > 0 else 0
        
        if error_rate > 5:  # More than 5 errors per hour
            issues.append({
                'type': 'high_error_rate',
                'severity': 'high',
                'description': f"High error rate: {error_rate:.1f} errors per hour",
                'impact': 'System reliability is compromised'
            })
        
        # Consistently failing components
        failing_components = [
            name for name, status in component_health.items()
            if not status['healthy'] and status.get('consecutive_failures', 0) >= 5
        ]
        
        if failing_components:
            issues.append({
                'type': 'component_failures',
                'severity': 'high',
                'description': f"Components with persistent failures: {', '.join(failing_components)}",
                'impact': 'Affected functionality may be unavailable'
            })
        
        # Low resolution rate
        resolution_rate = stats.get('resolution_rate_percent', 100)
        if resolution_rate < 30:
            issues.append({
                'type': 'low_resolution_rate',
                'severity': 'medium',
                'description': f"Low error resolution rate: {resolution_rate}%",
                'impact': 'Errors are not being resolved effectively'
            })
        
        return issues
    
    def _generate_recommendations(self, stats: Dict[str, Any], component_health: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on error analysis."""
        recommendations = []
        
        # High error rate recommendations
        total_errors = stats.get('total_errors', 0)
        if total_errors > 20:
            recommendations.append("Consider increasing error handling robustness and adding more validation")
        
        # Component-specific recommendations
        most_problematic = stats.get('most_problematic_component')
        if most_problematic:
            recommendations.append(f"Focus debugging efforts on {most_problematic} component")
        
        # Storage error recommendations
        storage_errors = stats.get('errors_by_category', {}).get('storage_failure', 0)
        if storage_errors > 5:
            recommendations.append("Check storage system health and consider increasing retry limits")
        
        # Data validation recommendations
        validation_errors = stats.get('errors_by_category', {}).get('data_validation', 0)
        if validation_errors > 3:
            recommendations.append("Improve input data validation and sanitization")
        
        # Resolution rate recommendations
        resolution_rate = stats.get('resolution_rate_percent', 100)
        if resolution_rate < 70:
            recommendations.append("Review error handling logic and improve automatic recovery mechanisms")
        
        # General recommendations
        if not recommendations:
            recommendations.append("System is operating normally - continue monitoring")
        
        return recommendations
    
    def _analyze_error_trends(self, hours: int) -> Dict[str, Any]:
        """Analyze error trends over the specified time period."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_errors = [
                e for e in self.error_handler.error_records 
                if e.timestamp >= cutoff_time
            ]
            
            if not recent_errors:
                return {'trend': 'stable', 'details': 'No errors in time period'}
            
            # Split time period in half to compare trends
            mid_time = cutoff_time + timedelta(hours=hours/2)
            
            first_half_errors = [e for e in recent_errors if e.timestamp < mid_time]
            second_half_errors = [e for e in recent_errors if e.timestamp >= mid_time]
            
            first_half_count = len(first_half_errors)
            second_half_count = len(second_half_errors)
            
            if second_half_count > first_half_count * 1.5:
                trend = 'increasing'
            elif second_half_count < first_half_count * 0.5:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'first_half_errors': first_half_count,
                'second_half_errors': second_half_count,
                'change_percentage': ((second_half_count - first_half_count) / max(1, first_half_count)) * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {'trend': 'unknown', 'error': str(e)}
    
    def _identify_trending_issues(self, errors: List[ErrorRecord]) -> List[Dict[str, Any]]:
        """Identify issues that are trending upward."""
        trending = []
        
        try:
            # Group errors by type and component
            error_groups = {}
            for error in errors:
                key = f"{error.component}:{error.exception_type}"
                if key not in error_groups:
                    error_groups[key] = []
                error_groups[key].append(error)
            
            # Find groups with increasing frequency
            for key, group_errors in error_groups.items():
                if len(group_errors) >= 3:  # Need at least 3 occurrences
                    # Check if errors are increasing over time
                    sorted_errors = sorted(group_errors, key=lambda x: x.timestamp)
                    
                    # Simple trend analysis: compare first and last third
                    third_size = len(sorted_errors) // 3
                    if third_size > 0:
                        first_third = sorted_errors[:third_size]
                        last_third = sorted_errors[-third_size:]
                        
                        # Calculate time spans
                        first_span = (first_third[-1].timestamp - first_third[0].timestamp).total_seconds()
                        last_span = (last_third[-1].timestamp - last_third[0].timestamp).total_seconds()
                        
                        # If errors are happening more frequently in recent period
                        if last_span > 0 and first_span > 0 and (first_span / last_span) > 1.5:
                            component, error_type = key.split(':', 1)
                            trending.append({
                                'component': component,
                                'error_type': error_type,
                                'total_occurrences': len(group_errors),
                                'trend_indicator': 'increasing_frequency'
                            })
            
            return trending
            
        except Exception as e:
            self.logger.error(f"Error identifying trending issues: {e}")
            return []
    
    def _rank_problematic_components(self, component_patterns: Dict[str, Any]) -> List[Tuple[str, int]]:
        """Rank components by how problematic they are."""
        try:
            component_scores = []
            
            for component, pattern in component_patterns.items():
                # Calculate problem score based on multiple factors
                score = 0
                
                # Base score from error count
                score += pattern['total_errors'] * 10
                
                # Penalty for low resolution rate
                resolution_rate = pattern.get('resolution_rate', 100)
                score += (100 - resolution_rate) * 2
                
                # Penalty for high retry count
                avg_retries = pattern.get('avg_retry_count', 0)
                score += avg_retries * 5
                
                # Penalty for critical errors
                critical_count = pattern.get('severity_distribution', {}).get('critical', 0)
                score += critical_count * 50
                
                component_scores.append((component, int(score)))
            
            # Sort by score (highest first)
            component_scores.sort(key=lambda x: x[1], reverse=True)
            
            return component_scores[:10]  # Top 10 most problematic
            
        except Exception as e:
            self.logger.error(f"Error ranking problematic components: {e}")
            return []


def create_error_monitor(error_handler: ErrorHandler) -> ErrorMonitor:
    """Factory function to create an error monitor."""
    return ErrorMonitor(error_handler)


def generate_daily_health_report(error_handler: ErrorHandler, output_dir: Path) -> bool:
    """Generate and save daily health report."""
    try:
        monitor = ErrorMonitor(error_handler)
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"health_report_{timestamp}.json"
        
        return monitor.export_error_report(report_path, hours=24)
        
    except Exception as e:
        logger.error(f"Error generating daily health report: {e}", exc_info=True)
        return False