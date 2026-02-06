from typing import Any, Dict, Optional

from src.bl.scoring.rules.base import IRule
from src.core import get_logger

logger = get_logger(__name__)


class RuleRegistration:
    def __init__(self, rule: IRule, weight: float, enabled: bool = True):
        self.rule = rule
        self.weight = weight
        self.enabled = enabled


class ScoringRuleRegistry:
    def __init__(self):
        self._rules: Dict[str, RuleRegistration] = {}
        self._security_rule: Optional[IRule] = None
        logger.debug("ScoringRuleRegistry initialized")

    def register(self, name: str, rule: IRule, weight: float, enabled: bool = True) -> None:
        if name in self._rules:
            logger.warning("Overwriting existing rule '%s'", name)

        self._rules[name] = RuleRegistration(rule, weight, enabled)
        logger.debug("Registered rule '%s' with weight %.2f", name, weight)

    def register_security_rule(self, rule: IRule) -> None:
        self._security_rule = rule
        logger.debug("Registered security rule")

    def unregister(self, name: str) -> None:
        if name in self._rules:
            del self._rules[name]
            logger.debug("Unregistered rule '%s'", name)

    def enable(self, name: str) -> None:
        if name in self._rules:
            self._rules[name].enabled = True
            logger.debug("Enabled rule '%s'", name)

    def disable(self, name: str) -> None:
        if name in self._rules:
            self._rules[name].enabled = False
            logger.debug("Disabled rule '%s'", name)

    def get_enabled_rules(self) -> Dict[str, IRule]:
        return {name: reg.rule for name, reg in self._rules.items() if reg.enabled}

    def get_all_rules(self) -> Dict[str, IRule]:
        return {name: reg.rule for name, reg in self._rules.items()}

    def get_weights(self) -> Dict[str, float]:
        return {name: reg.weight for name, reg in self._rules.items() if reg.enabled}

    def get_security_rule(self) -> Optional[IRule]:
        return self._security_rule

    def is_enabled(self, name: str) -> bool:
        return self._rules.get(name, None) is not None and self._rules[name].enabled

    def clear(self) -> None:
        self._rules.clear()
        self._security_rule = None
        logger.debug("Registry cleared")
