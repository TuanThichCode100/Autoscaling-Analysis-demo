"""
Utility functions for ML pipeline
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


def get_project_paths() -> Dict[str, Path]:
    """Get all important project paths"""
    base_dir = Path(__file__).parent.parent
    
    return {
        "base": base_dir,
        "data_raw": base_dir / "data" / "raw",
        "data_processed": base_dir / "data" / "processed",
        "models": base_dir / "models",
        "scripts": base_dir / "scripts",
        "notebooks": base_dir / "notebooks"
    }


def ensure_directories() -> Dict[str, Path]:
    """Ensure all required directories exist"""
    paths = get_project_paths()
    
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths


def save_config(config: Dict[str, Any], config_path: str = None):
    """Save configuration to JSON file"""
    if config_path is None:
        config_path = str(Path(__file__).parent.parent / "config.json")
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config saved to {config_path}")


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    if config_path is None:
        config_path = str(Path(__file__).parent.parent / "config.json")
    
    if not Path(config_path).exists():
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def setup_logging():
    """Setup logging configuration"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    return logging.getLogger(__name__)


# Default ML Pipeline Config
DEFAULT_CONFIG = {
    "data": {
        "resample_window": "60S",  # 1 minute
        "train_test_split": 0.8
    },
    "model": {
        "name": "lgb_model.pkl",
        "objective": "regression",
        "learning_rate": 0.05,
        "n_estimators": 500
    },
    "inference": {
        "min_data_points": 10,
        "forecast_steps": 5
    }
}
