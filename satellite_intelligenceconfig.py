"""
Configuration management for satellite intelligence system.
Handles Sentinel Hub API credentials, target coordinates, and collection intervals.
"""
import os
import json
from typing import Dict, Tuple, Any
from dataclasses import dataclass
from datetime import timedelta
import logging
from firebase_admin import credentials, initialize_app, firestore
import sentinelhub

logger = logging.getLogger(__name__)

@dataclass
class SatelliteConfig:
    """
    Central configuration class for satellite intelligence operations.
    
    Attributes:
        sentinelhub_client_id: Sentinel Hub OAuth client ID
        sentinelhub_client_secret: Sentinel Hub OAuth client secret
        sentinelhub_instance_id: Sentinel Hub instance ID
        firebase_project_id: Firebase project ID for state management
        firebase_credentials_path: Path to Firebase service account JSON
        target_coordinates: Dictionary of location names to (lat, lon) tuples
        collection_intervals: Dictionary of data type to collection frequency in minutes
        max_retries: Maximum number of retry attempts for failed requests
        retry_delay: Initial delay between retries in seconds
        bbox_size: Size of bounding box in degrees (lat, lon)
        resolution: Tuple of (width, height) for image resolution
    """
    sentinelhub_client_id: str
    sentinelhub_client_secret: str
    sentinelhub_instance_id: str
    firebase_project_id: str
    firebase_credentials_path: str
    target_coordinates: Dict[str, Tuple[float, float]]
    collection_intervals: Dict[str, int]
    max_retries: int = 3
    retry_delay: float = 1.0
    bbox_size: float = 0.01  # ~1km at equator
    resolution: Tuple[int, int] = (512, 512)
    
    def __post_init__(self):
        """Validate configuration and initialize Firebase."""
        self._validate_config()
        self._initialize_firebase()
        
    def _validate_config(self) -> None:
        """Validate all configuration parameters."""
        required_params = [
            ('sentinelhub_client_id', self.sentinelhub_client_id),
            ('sentinelhub_client_secret', self.sentinelhub_client_secret),
            ('sentinelhub_instance_id', self.sentinelhub_instance_id),
            ('firebase_project_id', self.firebase_project_id),
            ('firebase_credentials_path', self.firebase_credentials_path)
        ]
        
        for param_name, param_value in required_params:
            if not param_value:
                raise ValueError(f"Missing required parameter: {param_name}")
                
        if not os.path.exists(self.firebase_credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at: {self.firebase_credentials_path}"
            )
            
        # Validate target coordinates