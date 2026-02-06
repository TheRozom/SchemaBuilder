from typing import Any, Dict, Optional

from src.core import get_logger
from src.core.config import settings
from src.shared.models import SchemaNode, SchemaType
from src.shared.utils import tree_traversal

logger = get_logger(__name__)


class SecurityRule:
    def __init__(self) -> None:
        self.score_zero: bool = False
        self._issue_found: Optional[str] = None

    def evaluate(self, schema: Dict[str, Any]) -> float:
        self.score_zero = False
        self._issue_found = None
        max_nesting = settings.SECURITY_MAX_NESTING_DEPTH
        max_string_len = settings.SECURITY_MAX_STRING_LENGTH
        max_int_digits = settings.SECURITY_MAX_INTEGER_DIGITS

        def check_node(node_dict: Dict[str, Any], depth: int) -> Optional[bool]:
            if not isinstance(node_dict, dict):
                return None

            if depth > max_nesting:
                self.score_zero = True
                self._issue_found = f"Nesting depth exceeds {max_nesting}"
                logger.warning("Security issue: %s", self._issue_found)

                return False

            node = SchemaNode(**node_dict)

            if node.type == SchemaType.STRING:
                if node.maxLength and node.maxLength > max_string_len and not node.pattern:
                    self.score_zero = True
                    self._issue_found = (
                        f"String maxLength ({node.maxLength}) exceeds "
                        f"{max_string_len} without pattern"
                    )

                    logger.warning("Security issue: %s", self._issue_found)

                    return False

            if node.type in (SchemaType.INTEGER, SchemaType.NUMBER):
                if node.maximum and node.maximum > 10**max_int_digits:
                    self.score_zero = True
                    self._issue_found = f"Numeric maximum exceeds 10^{max_int_digits}"
                    logger.warning("Security issue: %s", self._issue_found)

                    return False

            return None

        tree_traversal.traverse_schema_node(schema, check_node)

        if self.score_zero:
            logger.info("Schema security check failed: %s", self._issue_found)

            return 0.0

        logger.debug("Schema passed security check")

        return 1.0
