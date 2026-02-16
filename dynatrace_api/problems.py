"""
Dynatrace Problems API Module - Enhanced with Service Correlation
Handle problem/issue detection with proper service filtering
"""
import requests
from typing import List, Dict, Optional
from config.settings import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DynatraceProblemsAPI:
    """Dynatrace Problems API handler with service correlation"""
    
    def __init__(self):
        self.base_url = config.DT_BASE_URL
        self.headers = config.get_auth_headers()
    
    def get_problems_for_service(
        self, 
        service_name: str,
        entity_id: str = None,
        timeframe: str = "24h"
    ) -> List[Dict]:
        """
        Get problems that are actually related to a specific service
        
        Args:
            service_name: Name of the service
            entity_id: The Dynatrace entity ID (for better filtering)
            timeframe: Time period to search (Dynatrace format)
            
        Returns:
            List of problem dictionaries that affect this service
        """
        url = f"{self.base_url}/api/v2/problems"
        
        # Build entity selector for the specific service
        if entity_id:
            # Use entity ID for precise filtering
            params = {
                "pageSize": 500,
                "from": f"now-{timeframe}",
                "entitySelector": f'type("SERVICE"),entityId("{entity_id}")',
                "fields": "+impactedEntities,+affectedEntities,+rootCauseEntity"
            }
        else:
            # Fallback to name-based search (less precise)
            params = {
                "pageSize": 500,
                "from": f"now-{timeframe}",
                "entitySelector": f'type("SERVICE"),entityName.contains("{service_name}")',
                "fields": "+impactedEntities,+affectedEntities,+rootCauseEntity"
            }
        
        try:
            logger.info(f"Fetching problems for service: {service_name} (entity: {entity_id})")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            all_problems = data.get("problems", [])
            
            # Filter problems to only those affecting this specific service
            if entity_id:
                service_problems = self._filter_problems_by_entity(all_problems, entity_id, service_name)
            else:
                service_problems = self._filter_problems_by_name(all_problems, service_name)
            
            logger.info(f"Found {len(service_problems)} problems (filtered from {len(all_problems)} total)")
            return service_problems
            
        except requests.RequestException as e:
            logger.error(f"Error fetching problems: {e}")
            return []
    
    def _filter_problems_by_entity(
        self, 
        problems: List[Dict], 
        entity_id: str,
        service_name: str
    ) -> List[Dict]:
        """
        Filter problems to only those that impact the specific service entity
        
        Args:
            problems: List of all problems
            entity_id: The service entity ID
            service_name: Service name for fallback matching
            
        Returns:
            Filtered list of problems
        """
        filtered_problems = []
        
        for problem in problems:
            # Check if this service is in impacted entities
            impacted = problem.get("impactedEntities", [])
            affected = problem.get("affectedEntities", [])
            root_cause = problem.get("rootCauseEntity", {})
            
            # Check all entity lists
            all_entities = impacted + affected
            if root_cause:
                all_entities.append(root_cause)
            
            # See if our service is in any of these lists
            for entity in all_entities:
                if entity.get("entityId", {}).get("id") == entity_id:
                    # This problem affects our service
                    problem["relevance"] = self._calculate_relevance(problem, entity_id)
                    filtered_problems.append(problem)
                    logger.debug(f"Problem '{problem.get('title')}' affects service {entity_id}")
                    break
                
                # Also check entity name as fallback
                entity_name = entity.get("name", "").lower()
                if service_name.lower() in entity_name:
                    problem["relevance"] = "name_match"
                    filtered_problems.append(problem)
                    logger.debug(f"Problem '{problem.get('title')}' matches service name")
                    break
        
        return filtered_problems
    
    def _filter_problems_by_name(
        self, 
        problems: List[Dict], 
        service_name: str
    ) -> List[Dict]:
        """
        Filter problems by service name (when entity ID is not available)
        
        Args:
            problems: List of all problems
            service_name: Service name to match
            
        Returns:
            Filtered list of problems
        """
        filtered_problems = []
        service_lower = service_name.lower()
        
        for problem in problems:
            # Check title and display name
            title = problem.get("title", "").lower()
            display_name = problem.get("displayName", "").lower()
            
            if service_lower in title or service_lower in display_name:
                problem["relevance"] = "title_match"
                filtered_problems.append(problem)
                continue
            
            # Check impacted/affected entities
            impacted = problem.get("impactedEntities", [])
            affected = problem.get("affectedEntities", [])
            
            for entity in impacted + affected:
                entity_name = entity.get("name", "").lower()
                if service_lower in entity_name:
                    problem["relevance"] = "entity_match"
                    filtered_problems.append(problem)
                    break
        
        return filtered_problems
    
    def _calculate_relevance(self, problem: Dict, entity_id: str) -> str:
        """
        Calculate how relevant a problem is to the service
        
        Args:
            problem: Problem dictionary
            entity_id: Service entity ID
            
        Returns:
            Relevance level: "root_cause", "directly_impacted", or "indirectly_affected"
        """
        # Check if service is the root cause
        root_cause = problem.get("rootCauseEntity", {})
        if root_cause.get("entityId", {}).get("id") == entity_id:
            return "root_cause"
        
        # Check if service is directly impacted
        impacted = problem.get("impactedEntities", [])
        for entity in impacted:
            if entity.get("entityId", {}).get("id") == entity_id:
                return "directly_impacted"
        
        # Service is in affected entities
        return "indirectly_affected"
    
    def get_all_open_problems(self, limit: int = 100) -> List[Dict]:
        """
        Get all currently open problems (for dashboard views)
        
        Args:
            limit: Maximum number of problems to return
            
        Returns:
            List of open problems
        """
        url = f"{self.base_url}/api/v2/problems"
        params = {
            "pageSize": limit,
            "problemSelector": "status(OPEN)"
        }
        
        try:
            logger.info("Fetching all open problems")
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            problems = data.get("problems", [])
            
            logger.info(f"Found {len(problems)} open problems")
            return problems
            
        except requests.RequestException as e:
            logger.error(f"Error fetching open problems: {e}")
            return []
    
    def categorize_problems(self, problems: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize problems by severity, status, and relevance
        
        Args:
            problems: List of problem dictionaries
            
        Returns:
            Categorized problems dictionary
        """
        categorized = {
            "critical": [],      # Root cause or high severity
            "important": [],     # Directly impacted
            "related": [],       # Indirectly affected
            "resolved": []       # Already resolved
        }
        
        for problem in problems:
            status = problem.get("status", "").upper()
            severity = problem.get("severityLevel", "").upper()
            relevance = problem.get("relevance", "unknown")
            
            if status == "RESOLVED":
                categorized["resolved"].append(problem)
            elif relevance == "root_cause" or severity in ["ERROR", "CUSTOM_ALERT"]:
                categorized["critical"].append(problem)
            elif relevance == "directly_impacted":
                categorized["important"].append(problem)
            else:
                categorized["related"].append(problem)
        
        return categorized
    
    def get_problem_details(self, problem_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific problem
        
        Args:
            problem_id: The problem ID
            
        Returns:
            Problem details or None
        """
        url = f"{self.base_url}/api/v2/problems/{problem_id}"
        
        try:
            logger.info(f"Fetching details for problem: {problem_id}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching problem details: {e}")
            return None
