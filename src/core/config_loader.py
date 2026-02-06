from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.logging import get_logger
from src.shared.exceptions import ConfigurationError

logger = get_logger(__name__)

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_yaml_config(
    filename: str,
    config_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    base_dir = config_dir or CONFIG_DIR
    config_path = base_dir / filename
    logger.debug("Loading config from %s", config_path)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.debug("Successfully loaded config: %s", filename)

            return data or {}

    except FileNotFoundError as e:
        logger.error("Config file not found: %s", config_path)
        raise ConfigurationError(
            message=f"Configuration file not found: {filename}",
            config_file=str(config_path),
        ) from e

    except yaml.YAMLError as e:
        logger.error("Invalid YAML in config %s: %s", filename, e)
        raise ConfigurationError(
            message=f"Invalid YAML in configuration file: {e}",
            config_file=str(config_path),
        ) from e


def get_config_path(filename: str) -> Path:
    return CONFIG_DIR / filename
