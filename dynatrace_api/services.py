"""
Dynatrace Services API Module
Handle service-related API calls
"""
import requests
from typing import Optional, List, Dict
from config.settings import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class DynatraceServicesAPI:
    """Dynatrace Services API handler"""
    
    def __init__(self):
        self.base_url = config.DT_BASE_URL
        self.headers = config.get_auth_headers()
    
    def get_service_entity_id(self, service_name: str) -> Optional[str]:
        """
        Get entity ID for a service by name
        
        Args:
            service_name: Name of the service to search for
            
        Returns:
            Entity ID if found, None otherwise
        """
        url = f"{self.base_url}/api/v2/entities"
        params = {
            "entitySelector": f'type(SERVICE),entityName.contains("{service_name}")',
            "pageSize": 1
        }
        
        try:
            logger.info(f"Searching for service: {service_name}")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            entities = response.json().get("entities", [])
            
            if not entities:
                logger.warning(f"No service found matching: {service_name}")
                return None
            
            entity_id = entities[0].get("entityId")
            logger.info(f"Found service ID: {entity_id}")
            return entity_id
            
        except requests.RequestException as e:
            logger.error(f"Error fetching service entity: {e}")
            return None
    
    def list_services(self, limit: int = 50) -> List[Dict]:
        """
        List all available services
        
        Args:
            limit: Maximum number of services to return
            
        Returns:
            List of service entities
        """
        url = f"{self.base_url}/api/v2/entities"
        params = {
            "entitySelector": "type(SERVICE)",
            "pageSize": limit,
            "fields": "+properties.serviceType,+toRelationships"
        }
        
        try:
            logger.info(f"Fetching up to {limit} services")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            entities = response.json().get("entities", [])
            logger.info(f"Found {len(entities)} services")
            return entities
            
        except requests.RequestException as e:
            logger.error(f"Error listing services: {e}")
            return []
    
    def get_service_details(self, entity_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific service
        
        Args:
            entity_id: The entity ID of the service
            
        Returns:
            Service details dictionary or None
        """
        url = f"{self.base_url}/api/v2/entities/{entity_id}"
        
        try:
            logger.info(f"Fetching details for entity: {entity_id}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching service details: {e}")
            return None
