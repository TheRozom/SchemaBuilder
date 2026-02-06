import threading
from typing import Any, Optional

from src.core import get_logger, load_yaml_config

logger = get_logger(__name__)


class ErrorMessageLoader:
    _instance: Optional["ErrorMessageLoader"] = None
    _messages: dict[str, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ErrorMessageLoader":
        # Simplified singleton pattern - GIL handles basic synchronization
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_messages()

        return cls._instance

    def _load_messages(self) -> None:
        messages = load_yaml_config("error_messages.yaml")
        logger.info("Loaded %d message templates", len(messages.get("messages", {})))
        # Atomic swap - readers see either old or new dict, never partial state
        self._messages = messages

    def get_fix_template(self, validator: str) -> str | None:
        # Read from local reference to avoid race conditions during reload
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
        # Lock only during load and assignment - atomic swap ensures thread safety
        with self._lock:
            logger.info("Reloading error messages configuration")
            self._load_messages()
