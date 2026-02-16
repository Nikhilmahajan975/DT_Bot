"""
Service Knowledge Base - Universal Data Layer
Collects and stores ALL service metrics and problems for intelligent querying
"""
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dynatrace_api.services import DynatraceServicesAPI
from dynatrace_api.metrics import DynatraceMetricsAPI
from dynatrace_api.problems import DynatraceProblemsAPI
from utils.logger import setup_logger
import threading

logger = setup_logger(__name__)

class ServiceKnowledgeBase:
    """
    Central knowledge base containing ALL service data
    Enables answering any comparative or analytical question
    """
    
    def __init__(self):
        self.services_api = DynatraceServicesAPI()
        self.metrics_api = DynatraceMetricsAPI()
        self.problems_api = DynatraceProblemsAPI()
        
        # Core data structures
        self.services = {}  # service_name -> complete service data
        self.problems_index = {}  # problem_id -> problem details
        self.service_by_entity = {}  # entity_id -> service_name (for lookups)
        self.aggregated_stats = {}
        
        # Metadata
        self.last_updated = None
        self.is_building = False
        self.build_error = None
        self._lock = threading.Lock()
    
    def build(self, timeframe: str = "2h", max_workers: int = 10):
        """
        Build complete knowledge base by fetching ALL data
        
        Args:
            timeframe: Time period for metrics (default 2h)
            max_workers: Parallel workers for fetching (default 10)
        """
        with self._lock:
            if self.is_building:
                logger.warning("Build already in progress, skipping...")
                return
            self.is_building = True
            self.build_error = None
        
        try:
            logger.info("🔄 Building service knowledge base...")
            start_time = time.time()
            
            # Step 1: Fetch all services
            logger.info("📋 Fetching service list...")
            services_list = self._fetch_all_services()
            logger.info(f"✅ Found {len(services_list)} services")
            
            # Step 2: Fetch metrics for all services in parallel
            logger.info("📊 Fetching metrics for all services (parallel)...")
            all_metrics = self._fetch_all_metrics_parallel(services_list, timeframe, max_workers)
            logger.info(f"✅ Retrieved metrics for {len(all_metrics)} services")
            
            # Step 3: Fetch all problems
            logger.info("🚨 Fetching all problems...")
            all_problems, service_problems_map = self._fetch_all_problems(timeframe)
            logger.info(f"✅ Found {len(all_problems)} problems")
            
            # Step 4: Build service records
            logger.info("🔨 Building service records...")
            self._build_service_records(services_list, all_metrics, service_problems_map)
            
            # Step 5: Calculate aggregates
            logger.info("📈 Calculating aggregate statistics...")
            self._calculate_aggregates()
            
            # Step 6: Finalize
            self.last_updated = datetime.now()
            elapsed = time.time() - start_time
            
            logger.info(f"✅ Knowledge base ready! {len(self.services)} services in {elapsed:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Error building knowledge base: {e}", exc_info=True)
            self.build_error = str(e)
        finally:
            with self._lock:
                self.is_building = False
    
    def _fetch_all_services(self) -> List[Dict]:
        """Fetch complete service list"""
        try:
            services = self.services_api.list_services(limit=200)
            return services
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            return []
    
    def _fetch_all_metrics_parallel(
        self, 
        services_list: List[Dict], 
        timeframe: str,
        max_workers: int
    ) -> Dict:
        """
        Fetch metrics for all services in parallel with rate limiting
        
        Returns:
            Dict mapping entity_id -> metrics
        """
        all_metrics = {}
        
        # Create batches to respect rate limits (10 at a time)
        batch_size = min(max_workers, 10)
        
        def fetch_service_metrics(service):
            """Helper to fetch metrics for one service"""
            entity_id = service.get('entityId')
            display_name = service.get('displayName', entity_id)
            
            try:
                metrics = self.metrics_api.get_service_metrics(entity_id, timeframe)
                insights = self.metrics_api.analyze_metrics(metrics)
                return entity_id, {
                    'metrics': metrics,
                    'insights': insights,
                    'display_name': display_name
                }
            except Exception as e:
                logger.warning(f"Failed to fetch metrics for {display_name}: {e}")
                return entity_id, None
        
        # Process in parallel batches
        for i in range(0, len(services_list), batch_size):
            batch = services_list[i:i+batch_size]
            
            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_service = {
                    executor.submit(fetch_service_metrics, svc): svc 
                    for svc in batch
                }
                
                for future in as_completed(future_to_service):
                    entity_id, result = future.result()
                    if result:
                        all_metrics[entity_id] = result
            
            # Small delay between batches to be nice to API
            if i + batch_size < len(services_list):
                time.sleep(0.5)
        
        return all_metrics
    
    def _fetch_all_problems(self, timeframe: str) -> tuple:
        """
        Fetch all problems and map to services
        
        Returns:
            (all_problems_list, service_to_problems_mapping)
        """
        try:
            # Get all open problems
            all_problems = self.problems_api.get_all_open_problems(limit=500)
            
            # Build service -> problems mapping
            service_problems = {}
            
            for problem in all_problems:
                # Get all affected services from the problem
                affected_entities = []
                
                # Check impacted entities
                for entity in problem.get('impactedEntities', []):
                    entity_id = entity.get('entityId', {}).get('id')
                    if entity_id and entity_id.startswith('SERVICE-'):
                        affected_entities.append(entity_id)
                
                # Check affected entities
                for entity in problem.get('affectedEntities', []):
                    entity_id = entity.get('entityId', {}).get('id')
                    if entity_id and entity_id.startswith('SERVICE-'):
                        affected_entities.append(entity_id)
                
                # Check root cause
                root_cause = problem.get('rootCauseEntity', {})
                root_id = root_cause.get('entityId', {}).get('id')
                if root_id and root_id.startswith('SERVICE-'):
                    affected_entities.append(root_id)
                
                # Map to services
                for entity_id in set(affected_entities):  # Remove duplicates
                    if entity_id not in service_problems:
                        service_problems[entity_id] = []
                    service_problems[entity_id].append(problem)
            
            return all_problems, service_problems
            
        except Exception as e:
            logger.error(f"Error fetching problems: {e}")
            return [], {}
    
    def _build_service_records(
        self,
        services_list: List[Dict],
        all_metrics: Dict,
        service_problems: Dict
    ):
        """Build complete service records"""
        for service in services_list:
            entity_id = service.get('entityId')
            display_name = service.get('displayName', entity_id)
            service_type = service.get('properties', {}).get('serviceType', 'Unknown')
            
            # Get metrics and problems
            metrics_data = all_metrics.get(entity_id, {})
            metrics = metrics_data.get('metrics', {})
            insights = metrics_data.get('insights', {})
            problems = service_problems.get(entity_id, [])
            
            # Calculate health score
            health_score = self._calculate_health_score(metrics, problems)
            
            # Determine status
            status = self._determine_status(insights.get('status', 'unknown'), problems)
            
            # Build complete record
            self.services[display_name] = {
                'entity_id': entity_id,
                'display_name': display_name,
                'type': service_type,
                'metrics': metrics,
                'problems': problems,
                'problem_count': len(problems),
                'health_score': health_score,
                'status': status,
                'insights': insights,
                'tags': service.get('tags', []),
                'management_zones': service.get('managementZones', [])
            }
            
            # Build reverse lookup
            self.service_by_entity[entity_id] = display_name
            
            # Index problems
            for problem in problems:
                problem_id = problem.get('problemId')
                if problem_id:
                    self.problems_index[problem_id] = problem
    
    def _calculate_health_score(self, metrics: Dict, problems: List) -> int:
        """
        Calculate 0-100 health score
        100 = perfect health, 0 = critical issues
        """
        score = 100.0
        
        # Deduct for errors
        error_count = metrics.get('error_count', 0)
        if isinstance(error_count, int):
            if error_count > 1000:
                score -= 40
            elif error_count > 500:
                score -= 30
            elif error_count > 100:
                score -= 20
            elif error_count > 10:
                score -= 10
        
        # Deduct for slow response time
        response_time = metrics.get('response_time', 0)
        if isinstance(response_time, (int, float)):
            if response_time > 2000:
                score -= 30
            elif response_time > 1000:
                score -= 20
            elif response_time > 500:
                score -= 10
        
        # Deduct for failure rate
        failure_rate = metrics.get('failure_rate', 0)
        if isinstance(failure_rate, (int, float)):
            if failure_rate > 10:
                score -= 40
            elif failure_rate > 5:
                score -= 25
            elif failure_rate > 2:
                score -= 15
            elif failure_rate > 1:
                score -= 5
        
        # Deduct for problems
        critical_problems = sum(1 for p in problems if p.get('severityLevel') in ['ERROR', 'CUSTOM_ALERT'])
        score -= critical_problems * 15
        score -= (len(problems) - critical_problems) * 8
        
        return max(0, int(score))
    
    def _determine_status(self, insights_status: str, problems: List) -> str:
        """Determine overall service status"""
        critical_problems = [p for p in problems if p.get('severityLevel') in ['ERROR', 'CUSTOM_ALERT']]
        
        if critical_problems or insights_status == 'critical':
            return 'critical'
        elif problems or insights_status == 'warning':
            return 'warning'
        else:
            return 'healthy'
    
    def _calculate_aggregates(self):
        """Calculate aggregate statistics across all services"""
        total = len(self.services)
        
        if total == 0:
            self.aggregated_stats = {}
            return
        
        healthy = sum(1 for s in self.services.values() if s['status'] == 'healthy')
        warning = sum(1 for s in self.services.values() if s['status'] == 'warning')
        critical = sum(1 for s in self.services.values() if s['status'] == 'critical')
        
        health_scores = [s['health_score'] for s in self.services.values()]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        total_problems = sum(s['problem_count'] for s in self.services.values())
        services_with_problems = sum(1 for s in self.services.values() if s['problem_count'] > 0)
        
        # Calculate metric averages
        error_counts = [s['metrics'].get('error_count', 0) for s in self.services.values() 
                       if isinstance(s['metrics'].get('error_count'), int)]
        avg_errors = sum(error_counts) / len(error_counts) if error_counts else 0
        
        response_times = [s['metrics'].get('response_time', 0) for s in self.services.values() 
                         if isinstance(s['metrics'].get('response_time'), (int, float))]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        self.aggregated_stats = {
            'total_services': total,
            'healthy_count': healthy,
            'warning_count': warning,
            'critical_count': critical,
            'healthy_percentage': (healthy / total * 100) if total > 0 else 0,
            'avg_health_score': round(avg_health, 1),
            'total_problems': total_problems,
            'services_with_problems': services_with_problems,
            'avg_error_count': round(avg_errors, 1),
            'avg_response_time': round(avg_response_time, 1),
            'last_updated': self.last_updated
        }
    
    def get_service(self, service_name: str) -> Optional[Dict]:
        """Get complete data for a specific service"""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict:
        """Get all service data"""
        return self.services
    
    def get_stats(self) -> Dict:
        """Get aggregate statistics"""
        return self.aggregated_stats
    
    def is_ready(self) -> bool:
        """Check if knowledge base is ready"""
        return self.last_updated is not None and not self.is_building
    
    def get_status(self) -> Dict:
        """Get knowledge base status"""
        return {
            'is_ready': self.is_ready(),
            'is_building': self.is_building,
            'last_updated': self.last_updated,
            'service_count': len(self.services),
            'error': self.build_error
        }
