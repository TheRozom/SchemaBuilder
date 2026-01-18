import threading
from typing import Any, Dict, Optional

from src.core import get_logger, load_yaml_config

logger = get_logger(__name__)


class ErrorMessageLoader:

    _instance: Optional["ErrorMessageLoader"] = None
    _messages: Dict[str, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ErrorMessageLoader":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_messages()
        return cls._instance

    def _load_messages(self) -> None:
        self._messages = load_yaml_config("error_messages.yaml")
        logger.info(
            "Loaded %d message templates", len(self._messages.get("messages", {}))
        )

    def get_fix_template(self, validator: str) -> Optional[str]:
        messages = self._messages.get("messages", {})
        validator_config = messages.get(validator, {})
        return validator_config.get("fix")

    def get_fallback_fix(self) -> str:
        defaults = self._messages.get("defaults", {})
        return defaults.get("fallback_fix", "")

    def get_default(self, key: str) -> str:
        defaults = self._messages.get("defaults", {})
        return defaults.get(key, "")

    def reload(self) -> None:
        with self._lock:
            logger.info("Reloading error messages configuration")
            self._load_messages()
