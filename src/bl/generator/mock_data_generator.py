"""Mock data generation using Faker and semantic understanding."""

from typing import Any, Dict, List, Optional, Union
from faker import Faker
import random
import re
from datetime import datetime, timedelta


class MockDataGenerator:
    """Generates realistic mock data based on field types and schemas."""

    def __init__(self, locale: str = "en_US", seed: Optional[int] = None):
        """
        Initialize mock data generator.

        Args:
            locale: Faker locale for data generation
            seed: Random seed for reproducibility
        """
        self.faker = Faker(locale)
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

    def generate_by_type(self, field_type: str, field_name: Optional[str] = None) -> Any:
        """
        Generate mock data for a specific field type.

        Args:
            field_type: The detected or specified field type
            field_name: Optional field name for context

        Returns:
            Generated mock data value
        """
        generators = {
            "email": self.faker.email,
            "name": self.faker.name,
            "phone": self.faker.phone_number,
            "address": self.faker.address,
            "city": self.faker.city,
            "country": self.faker.country,
            "zipcode": self.faker.zipcode,
            "date": lambda: self.faker.date(),
            "url": self.faker.url,
            "company": self.faker.company,
            "job": self.faker.job,
            "price": lambda: round(random.uniform(1, 1000), 2),
            "id": lambda: self.faker.uuid4(),
            "description": lambda: self.faker.text(max_nb_chars=200),
            "boolean": lambda: random.choice([True, False]),
        }

        generator = generators.get(field_type)
        if generator:
            return generator()

        # Fallback based on field name patterns
        if field_name:
            return self._generate_by_name_pattern(field_name)

        return None

    def _generate_by_name_pattern(self, field_name: str) -> Any:
        """Generate data based on field name patterns."""
        field_lower = field_name.lower()

        if "first" in field_lower and "name" in field_lower:
            return self.faker.first_name()
        elif "last" in field_lower and "name" in field_lower:
            return self.faker.last_name()
        elif "street" in field_lower:
            return self.faker.street_address()
        elif "state" in field_lower:
            return self.faker.state()
        elif "province" in field_lower:
            return self.faker.state()
        elif "username" in field_lower or "user_name" in field_lower:
            return self.faker.user_name()
        elif "password" in field_lower:
            return self.faker.password()
        elif "age" in field_lower:
            return random.randint(18, 80)
        elif "year" in field_lower:
            return random.randint(1950, datetime.now().year)
        elif "month" in field_lower:
            return random.randint(1, 12)
        elif "day" in field_lower:
            return random.randint(1, 28)
        elif "title" in field_lower:
            return self.faker.sentence(nb_words=4).rstrip(".")
        elif "comment" in field_lower or "note" in field_lower:
            return self.faker.sentence(nb_words=10)
        elif "code" in field_lower:
            return self.faker.bothify(text="??##??##")

        return self.faker.word()

    def generate_from_schema(
        self, schema: Dict[str, Any], count: int = 1
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate mock data from a JSON schema.

        Args:
            schema: JSON schema definition
            count: Number of records to generate

        Returns:
            Generated mock data (single dict if count=1, list otherwise)
        """
        if count == 1:
            return self._generate_single_record(schema)

        return [self._generate_single_record(schema) for _ in range(count)]

    def _generate_single_record(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single record from schema."""
        record = {}
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            value = self._generate_value_from_field_schema(field_name, field_schema)
            record[field_name] = value

        return record

    def _generate_value_from_field_schema(
        self, field_name: str, field_schema: Dict[str, Any]
    ) -> Any:
        """Generate a value based on field schema."""
        field_type = field_schema.get("type")
        field_format = field_schema.get("format")
        pattern = field_schema.get("pattern")
        enum = field_schema.get("enum")

        # Handle enum
        if enum:
            return random.choice(enum)

        # Handle by format
        if field_format:
            value = self._generate_by_format(field_format)
            if value is not None:
                return value

        # Handle by pattern
        if pattern:
            value = self._generate_by_pattern(pattern, field_name)
            if value is not None:
                return value

        # Handle by type
        if field_type == "string":
            return self._generate_string_value(field_name, field_schema)
        elif field_type == "integer":
            return self._generate_integer_value(field_schema)
        elif field_type == "number":
            return self._generate_number_value(field_schema)
        elif field_type == "boolean":
            return random.choice([True, False])
        elif field_type == "array":
            return self._generate_array_value(field_name, field_schema)
        elif field_type == "object":
            return self._generate_single_record(field_schema)
        elif field_type == "null":
            return None

        # Fallback
        return self._generate_by_name_pattern(field_name)

    def _generate_by_format(self, format_type: str) -> Optional[Any]:
        """Generate value based on JSON Schema format."""
        format_generators = {
            "email": self.faker.email,
            "uri": self.faker.url,
            "url": self.faker.url,
            "date": lambda: self.faker.date(),
            "date-time": lambda: self.faker.iso8601(),
            "time": lambda: self.faker.time(),
            "ipv4": self.faker.ipv4,
            "ipv6": self.faker.ipv6,
            "uuid": lambda: self.faker.uuid4(),
            "hostname": self.faker.domain_name,
        }

        generator = format_generators.get(format_type)
        return generator() if generator else None

    def _generate_by_pattern(self, pattern: str, field_name: str) -> Optional[Any]:
        """Generate value matching a regex pattern (simple patterns only)."""
        # Handle common simple patterns
        if pattern == r"^\d+$":
            return str(random.randint(1000, 9999))
        elif pattern == r"^[a-zA-Z]+$":
            return self.faker.word()
        elif pattern == r"^[a-zA-Z0-9]+$":
            return self.faker.bothify(text="????####")

        # For complex patterns, fall back to name-based generation
        return self._generate_by_name_pattern(field_name)

    def _generate_string_value(self, field_name: str, field_schema: Dict[str, Any]) -> str:
        """Generate string value with length constraints."""
        min_length = field_schema.get("minLength", 1)
        max_length = field_schema.get("maxLength", 100)

        # Generate based on field name
        value = str(self._generate_by_name_pattern(field_name))

        # Adjust length if needed
        if len(value) < min_length:
            value = value + self.faker.text(max_nb_chars=min_length - len(value))
        elif len(value) > max_length:
            value = value[:max_length]

        return value

    def _generate_integer_value(self, field_schema: Dict[str, Any]) -> int:
        """Generate integer value with constraints."""
        minimum = field_schema.get("minimum", 0)
        maximum = field_schema.get("maximum", 100)
        exclusive_min = field_schema.get("exclusiveMinimum")
        exclusive_max = field_schema.get("exclusiveMaximum")

        if exclusive_min is not None:
            minimum = exclusive_min + 1
        if exclusive_max is not None:
            maximum = exclusive_max - 1

        return random.randint(minimum, maximum)

    def _generate_number_value(self, field_schema: Dict[str, Any]) -> float:
        """Generate float value with constraints."""
        minimum = field_schema.get("minimum", 0.0)
        maximum = field_schema.get("maximum", 100.0)
        exclusive_min = field_schema.get("exclusiveMinimum")
        exclusive_max = field_schema.get("exclusiveMaximum")

        if exclusive_min is not None:
            minimum = exclusive_min + 0.01
        if exclusive_max is not None:
            maximum = exclusive_max - 0.01

        return round(random.uniform(minimum, maximum), 2)

    def _generate_array_value(self, field_name: str, field_schema: Dict[str, Any]) -> List[Any]:
        """Generate array value."""
        items_schema = field_schema.get("items", {})
        min_items = field_schema.get("minItems", 1)
        max_items = field_schema.get("maxItems", 5)

        array_length = random.randint(min_items, max_items)

        if isinstance(items_schema, dict):
            # All items follow the same schema
            return [
                self._generate_value_from_field_schema(f"{field_name}_item", items_schema)
                for _ in range(array_length)
            ]
        elif isinstance(items_schema, list):
            # Tuple validation - each position has its own schema
            return [
                self._generate_value_from_field_schema(f"{field_name}_item_{i}", schema)
                for i, schema in enumerate(items_schema[:array_length])
            ]

        # Fallback
        return [self.faker.word() for _ in range(array_length)]

    def generate_from_examples(
        self, examples: List[Dict[str, Any]], count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate mock data based on example data.

        Args:
            examples: List of example records
            count: Number of records to generate

        Returns:
            List of generated records
        """
        if not examples:
            return []

        # Analyze field types from examples
        field_types = self._infer_field_types_from_examples(examples)

        # Generate records
        return [
            {
                field: self._generate_similar_value(field, examples, field_types.get(field))
                for field in field_types.keys()
            }
            for _ in range(count)
        ]

    def _infer_field_types_from_examples(self, examples: List[Dict[str, Any]]) -> Dict[str, type]:
        """Infer field types from example records."""
        if not examples:
            return {}

        field_types = {}
        first_record = examples[0]

        for field in first_record.keys():
            values = [ex.get(field) for ex in examples if field in ex]
            if values:
                # Get the most common type
                types = [type(v) for v in values if v is not None]
                if types:
                    field_types[field] = max(set(types), key=types.count)

        return field_types

    def _generate_similar_value(
        self, field: str, examples: List[Dict[str, Any]], field_type: Optional[type]
    ) -> Any:
        """Generate a value similar to examples."""
        # Get sample values
        sample_values = [ex.get(field) for ex in examples if field in ex]

        if not sample_values:
            return None

        # For strings, try to detect patterns
        if field_type == str:
            # Check if it looks like a specific type
            sample_str = str(sample_values[0])
            if "@" in sample_str:
                return self.faker.email()
            elif sample_str.startswith("http"):
                return self.faker.url()
            else:
                return self._generate_by_name_pattern(field)

        # For numbers, generate in similar range
        elif field_type in (int, float):
            min_val = min(v for v in sample_values if isinstance(v, (int, float)))
            max_val = max(v for v in sample_values if isinstance(v, (int, float)))

            if field_type == int:
                return random.randint(int(min_val), int(max_val))
            else:
                return round(random.uniform(float(min_val), float(max_val)), 2)

        # For booleans
        elif field_type == bool:
            return random.choice([True, False])

        # For lists
        elif field_type == list:
            if sample_values:
                sample_list = sample_values[0]
                if sample_list:
                    length = len(sample_list)
                    item_type = type(sample_list[0])
                    return [self.faker.word() for _ in range(length)]
            return []

        return None
