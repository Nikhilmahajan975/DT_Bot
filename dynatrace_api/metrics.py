"""
Dynatrace Metrics API Module
Handle metrics-related API calls with proper error handling
"""
import requests
from typing import Dict, Optional
from config.settings import config
from utils.logger import setup_logger
from utils.timeframe import timeframe_to_dynatrace

logger = setup_logger(__name__)

class DynatraceMetricsAPI:
    """Dynatrace Metrics API handler"""
    
    def __init__(self):
        self.base_url = config.DT_BASE_URL
        self.headers = config.get_auth_headers()
        
        # Define available metrics
        self.metric_keys = [
            "builtin:service.errors.total.count",
            "builtin:service.response.time",
            "builtin:service.requestCount.total",
            "builtin:service.errors.total.rate"
        ]
    
    def get_service_metrics(
        self, 
        entity_id: str, 
        timeframe: str = "2h"
    ) -> Dict[str, any]:
        """
        Fetch service metrics for a given entity
        
        Args:
            entity_id: The Dynatrace entity ID
            timeframe: Time period (e.g., "2h", "30m", "7d")
            
        Returns:
            Dictionary containing metric values
        """
        url = f"{self.base_url}/api/v2/metrics/query"
        
        try:
            from_time_str, to_time_str = timeframe_to_dynatrace(timeframe)
        except ValueError as e:
            logger.error(f"Invalid timeframe: {e}")
            return self._empty_metrics()
        
        params = {
            "metricSelector": ",".join(self.metric_keys),
            "resolution": "Inf",
            "from": from_time_str,
            "to": to_time_str,
            "entitySelector": f"entityId({entity_id})"
        }
        
        try:
            logger.info(f"Fetching metrics for entity {entity_id}")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_metrics_response(data)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching metrics: {e}")
            return self._empty_metrics()
    
    def _parse_metrics_response(self, data: Dict) -> Dict[str, any]:
        """
        Parse the metrics API response
        
        Args:
            data: Raw API response
            
        Returns:
            Formatted metrics dictionary
        """
        metrics_result = {
            "error_count": "N/A",
            "response_time": "N/A",
            "request_count": "N/A",
            "failure_rate": "N/A"
        }
        
        for metric in data.get("result", []):
            metric_id = metric.get("metricId", "")
            
            for data_point in metric.get("data", []):
                values = data_point.get("values", [])
                if not values:
                    continue
                
                value = values[0]
                
                if metric_id == "builtin:service.errors.total.count":
                    metrics_result["error_count"] = int(value)
                elif metric_id == "builtin:service.response.time":
                    metrics_result["response_time"] = round(value, 2)
                elif metric_id == "builtin:service.requestCount.total":
                    metrics_result["request_count"] = int(value)
                elif metric_id == "builtin:service.errors.total.rate":
                    metrics_result["failure_rate"] = round(value * 100, 2)
        
        logger.info(f"Parsed metrics: {metrics_result}")
        return metrics_result
    
    def _empty_metrics(self) -> Dict[str, any]:
        """Return empty metrics structure"""
        return {
            "error_count": "N/A",
            "response_time": "N/A",
            "request_count": "N/A",
            "failure_rate": "N/A"
        }
    
    def analyze_metrics(self, metrics: Dict) -> Dict[str, str]:
        """
        Analyze metrics and provide insights
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Analysis results with insights
        """
        insights = {
            "status": "healthy",
            "concerns": [],
            "recommendations": []
        }
        
        # Check error rate
        if isinstance(metrics.get("failure_rate"), (int, float)):
            if metrics["failure_rate"] > 5:
                insights["status"] = "critical"
                insights["concerns"].append(
                    f"High failure rate: {metrics['failure_rate']}%"
                )
                insights["recommendations"].append(
                    "Investigate error logs and recent deployments"
                )
            elif metrics["failure_rate"] > 1:
                insights["status"] = "warning"
                insights["concerns"].append(
                    f"Elevated failure rate: {metrics['failure_rate']}%"
                )
        
        # Check response time
        if isinstance(metrics.get("response_time"), (int, float)):
            if metrics["response_time"] > 1000:
                if insights["status"] == "healthy":
                    insights["status"] = "warning"
                insights["concerns"].append(
                    f"Slow response time: {metrics['response_time']} ms"
                )
                insights["recommendations"].append(
                    "Review service performance and database queries"
                )
        
        # Check error count
        if isinstance(metrics.get("error_count"), int):
            if metrics["error_count"] > 100:
                insights["concerns"].append(
                    f"High error count: {metrics['error_count']}"
                )
        
        if not insights["concerns"]:
            insights["recommendations"].append(
                "Service metrics look healthy. Continue monitoring."
            )
        
        return insights
