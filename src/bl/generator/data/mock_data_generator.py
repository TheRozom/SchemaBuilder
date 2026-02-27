import random
from copy import deepcopy
from typing import Any

from faker import Faker
from jsonschema import Draft7Validator

from src.bl.generator.config import get_default_ranges
from src.bl.generator.strategies import (
    EnumStrategy,
    FieldNameStrategy,
    PatternStrategy,
    TypeStrategy,
    ValueGenerationStrategy,
)
from src.core import get_logger
from src.shared.exceptions import MockDataGenerationError
from src.shared.utils import strip_required_keywords

MAX_VALIDATION_RETRIES = 5


class MockDataGenerator:
    def __init__(self, locale: str = "en_US", seed: int | None = None):
        self.faker = Faker(locale)
        self._defaults = get_default_ranges()
        self.logger = get_logger(__name__)

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        self._setup_strategies()

    def _setup_strategies(self) -> None:
        field_name_strategy = FieldNameStrategy(self.faker)
        self.strategies: list[ValueGenerationStrategy] = [
            EnumStrategy(),
            PatternStrategy(self.faker),
            TypeStrategy(
                self.faker,
                field_name_strategy,
                self._generate_value,
                self._generate_single_record,
            ),
            field_name_strategy,
        ]
        self._mode = "meaningful"
        self._min_populated_fields = 1
        self._null_probability = 0.1

    def generate_from_schema(
        self,
        schema: dict[str, Any],
        count: int = 1,
        mode: str = "meaningful",
        min_populated_fields: int = 1,
        null_probability: float = 0.1,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if count < 1:
            raise ValueError("count must be at least 1")
        if count > 10000:
            raise ValueError("count exceeds maximum allowed value of 10000")
        if mode not in {"meaningful", "strict_valid"}:
            raise ValueError("mode must be either 'meaningful' or 'strict_valid'")
        if min_populated_fields < 1:
            raise ValueError("min_populated_fields must be at least 1")
        if not 0 <= null_probability <= 1:
            raise ValueError("null_probability must be between 0 and 1")

        self._mode = mode
        self._min_populated_fields = min_populated_fields
        self._null_probability = null_probability
        schema = strip_required_keywords(schema)

        validator = Draft7Validator(schema)

        if count == 1:
            return self._generate_valid_record(schema, validator)
        return [self._generate_valid_record(schema, validator) for _ in range(count)]

    def _generate_valid_record(
        self, schema: dict[str, Any], validator: Draft7Validator
    ) -> dict[str, Any]:
        last_errors = []
        for attempt in range(MAX_VALIDATION_RETRIES):
            resolved_schema = self._resolve_top_level_composition(schema)
            record = self._generate_single_record(resolved_schema, resolve_composition=False)
            last_errors = list(validator.iter_errors(record))
            if not last_errors and self._is_meaningful_record(record, resolved_schema):
                return record
            if not last_errors and self._mode == "meaningful":
                self.logger.debug(
                    "Generated record was valid but not meaningful (attempt %d/%d)",
                    attempt + 1,
                    MAX_VALIDATION_RETRIES,
                )
                continue
            self.logger.debug(
                "Generated record failed validation (attempt %d/%d): %s",
                attempt + 1,
                MAX_VALIDATION_RETRIES,
                [e.message for e in last_errors],
            )
        raise MockDataGenerationError(
            message=f"Failed to generate valid mock data after {MAX_VALIDATION_RETRIES} attempts",
            validation_errors=[e.message for e in last_errors],
        )

    def _resolve_top_level_composition(self, schema: dict[str, Any]) -> dict[str, Any]:
        if "properties" in schema:
            return schema

        if "allOf" in schema:
            return self._merge_all_of(schema["allOf"])

        for keyword in ("anyOf", "oneOf"):
            if keyword in schema:
                return self._pick_preferred_schema(schema[keyword])

        return schema

    def _generate_single_record(
        self, schema: dict[str, Any], resolve_composition: bool = True
    ) -> dict[str, Any]:
        if resolve_composition:
            schema = self._resolve_top_level_composition(schema)
        record = {}
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            record[field_name] = self._generate_value(field_name, field_schema)

        if self._mode == "meaningful" and properties:
            candidate_keys = [
                key
                for key, field_schema in properties.items()
                if self._field_can_be_populated(field_schema)
            ]
            min_target = min(self._min_populated_fields, len(candidate_keys))
            if min_target and self._count_populated_fields(record, candidate_keys) < min_target:
                fallback_candidates = list(candidate_keys)
                random.shuffle(fallback_candidates)
                for key in fallback_candidates:
                    record[key] = self._generate_value(key, properties[key])
                    if self._count_populated_fields(record, candidate_keys) >= min_target:
                        break

        return record

    def _generate_value(self, field_name: str, field_schema: dict[str, Any]) -> Any:
        if "allOf" in field_schema:
            merged = self._merge_all_of(field_schema["allOf"])
            return self._generate_value(field_name, merged)

        for keyword in ("anyOf", "oneOf"):
            sub_schemas = field_schema.get(keyword, [])
            if sub_schemas:
                chosen = self._pick_preferred_schema(sub_schemas)
                return self._generate_value(field_name, chosen)

        if field_schema.get("type") == "null":
            return None

        null_possible = self._null_is_possible(field_schema)

        for strategy in self.strategies:
            if strategy.can_generate(field_name, field_schema):
                value = strategy.generate(field_name, field_schema)
                if value is not None or field_schema.get("type") == "null" or null_possible:
                    return value

        return self.faker.word()

    @staticmethod
    def _null_is_possible(field_schema: dict[str, Any]) -> bool:
        for keyword in ("anyOf", "oneOf"):
            for sub in field_schema.get(keyword, []):
                if sub.get("type") == "null":
                    return True
        return False

    def _merge_all_of(self, sub_schemas: list[dict[str, Any]]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for sub in sub_schemas:
            merged = self._merge_schema_constraints(merged, sub)
        return merged

    def _merge_schema_constraints(
        self, first: dict[str, Any], second: dict[str, Any]
    ) -> dict[str, Any]:
        merged: dict[str, Any] = deepcopy(first)

        for key, second_value in second.items():
            if key not in merged:
                merged[key] = deepcopy(second_value)
                continue

            first_value = merged[key]

            if (
                key == "properties"
                and isinstance(first_value, dict)
                and isinstance(second_value, dict)
            ):
                merged_properties = dict(first_value)
                for prop_name, prop_schema in second_value.items():
                    if (
                        prop_name in merged_properties
                        and isinstance(merged_properties[prop_name], dict)
                        and isinstance(prop_schema, dict)
                    ):
                        merged_properties[prop_name] = self._merge_schema_constraints(
                            merged_properties[prop_name], prop_schema
                        )
                    else:
                        merged_properties[prop_name] = deepcopy(prop_schema)
                merged[key] = merged_properties
                continue

            if key in {"minimum", "exclusiveMinimum", "minLength", "minItems"}:
                merged[key] = max(first_value, second_value)
                continue

            if key in {"maximum", "exclusiveMaximum", "maxLength", "maxItems"}:
                merged[key] = min(first_value, second_value)
                continue

            if key == "enum" and isinstance(first_value, list) and isinstance(second_value, list):
                allowed = set(second_value)
                merged[key] = [value for value in first_value if value in allowed]
                continue

            merged[key] = deepcopy(second_value)

        return merged

    def _pick_preferred_schema(self, sub_schemas: list[dict[str, Any]]) -> dict[str, Any]:
        if not sub_schemas:
            return {}

        null_schemas = [s for s in sub_schemas if s.get("type") == "null"]
        non_null_schemas = [s for s in sub_schemas if s.get("type") != "null"]

        if null_schemas and non_null_schemas:
            if random.random() < self._null_probability:
                return random.choice(null_schemas)
            candidates = non_null_schemas
        else:
            candidates = sub_schemas

        max_score = max(self._schema_richness_score(s) for s in candidates)
        richest = [s for s in candidates if self._schema_richness_score(s) == max_score]
        return random.choice(richest)

    @staticmethod
    def _schema_richness_score(schema: dict[str, Any]) -> int:
        score = 0
        schema_type = schema.get("type")
        properties = schema.get("properties", {})

        if schema_type == "object":
            score += 10
        if schema_type == "array":
            score += 5
        score += len(properties) * 2
        if schema.get("enum"):
            score += 2
        if any(
            key in schema
            for key in ("pattern", "minLength", "maxLength", "minimum", "maximum", "minItems")
        ):
            score += 1
        return score

    def _is_meaningful_record(self, record: dict[str, Any], schema: dict[str, Any]) -> bool:
        if self._mode != "meaningful":
            return True

        resolved = self._resolve_top_level_composition(schema)
        properties = resolved.get("properties", {})

        if not properties:
            return True

        candidate_keys = [
            key
            for key, field_schema in properties.items()
            if self._field_can_be_populated(field_schema)
        ]
        if not candidate_keys:
            return True

        min_target = min(self._min_populated_fields, len(candidate_keys))
        return self._count_populated_fields(record, candidate_keys) >= min_target

    @staticmethod
    def _count_populated_fields(record: dict[str, Any], keys: list[str] | None = None) -> int:
        populated = 0
        values = record.values() if keys is None else [record.get(key) for key in keys]
        for value in values:
            if value is None:
                continue
            if isinstance(value, (str, list, dict)) and len(value) == 0:
                continue
            populated += 1
        return populated

    def _field_can_be_populated(self, field_schema: dict[str, Any]) -> bool:
        schema_type = field_schema.get("type")
        if schema_type == "null":
            return False

        if "allOf" in field_schema:
            merged = self._merge_all_of(field_schema["allOf"])
            return self._field_can_be_populated(merged)

        for keyword in ("anyOf", "oneOf"):
            sub_schemas = field_schema.get(keyword, [])
            if sub_schemas:
                return any(self._field_can_be_populated(sub) for sub in sub_schemas)

        return True
