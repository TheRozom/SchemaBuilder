import pytest

from src.bl.builder.normalizers import BoundNormalizer
from src.shared.models import SchemaNode, SchemaType


class TestSmartMaximumPositiveIntegers:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_small_integer(self):
        assert self.normalizer.smart_maximum(7) == 7

    def test_integer_in_10_49_range(self):
        assert self.normalizer.smart_maximum(23) == 25

    def test_integer_in_50_99_range(self):
        assert self.normalizer.smart_maximum(73) == 80

    def test_integer_at_boundary_100(self):
        assert self.normalizer.smart_maximum(100) == 100

    def test_large_integer(self):
        assert self.normalizer.smart_maximum(947) == 1000

    def test_very_large_integer(self):
        assert self.normalizer.smart_maximum(15400) == 20000

    def test_exact_step_boundary(self):
        assert self.normalizer.smart_maximum(500) == 500

    def test_integer_returns_int(self):
        result = self.normalizer.smart_maximum(947)
        assert isinstance(result, int)


class TestSmartMaximumPositiveFloats:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_float_over_100(self):
        assert self.normalizer.smart_maximum(947.5) == 1000.0

    def test_small_decimal(self):
        assert self.normalizer.smart_maximum(0.0037) == 0.004

    def test_decimal_under_one(self):
        assert self.normalizer.smart_maximum(0.15) == 0.2

    def test_float_returns_float(self):
        result = self.normalizer.smart_maximum(947.5)
        assert isinstance(result, float)

    def test_float_in_10_49_range(self):
        assert self.normalizer.smart_maximum(23.7) == 25.0


class TestSmartMinimumPositiveValues:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_small_integer(self):
        assert self.normalizer.smart_minimum(7) == 7

    def test_integer_in_10_49_range(self):
        assert self.normalizer.smart_minimum(23) == 20

    def test_integer_in_50_99_range(self):
        assert self.normalizer.smart_minimum(73) == 70

    def test_large_integer(self):
        assert self.normalizer.smart_minimum(947) == 900

    def test_very_large_integer(self):
        assert self.normalizer.smart_minimum(15400) == 10000

    def test_small_decimal(self):
        assert self.normalizer.smart_minimum(0.0037) == 0.003

    def test_integer_returns_int(self):
        result = self.normalizer.smart_minimum(947)
        assert isinstance(result, int)


class TestZeroAndNone:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_maximum_zero(self):
        assert self.normalizer.smart_maximum(0) == 0

    def test_minimum_zero(self):
        assert self.normalizer.smart_minimum(0) == 0

    def test_maximum_none(self):
        assert self.normalizer.smart_maximum(None) is None

    def test_minimum_none(self):
        assert self.normalizer.smart_minimum(None) is None


class TestNegativeValues:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_negative_maximum_rounds_toward_zero(self):
        result = self.normalizer.smart_maximum(-23)
        assert result == -20

    def test_negative_minimum_rounds_away_from_zero(self):
        result = self.normalizer.smart_minimum(-23)
        assert result == -25

    def test_negative_large_maximum(self):
        result = self.normalizer.smart_maximum(-947)
        assert result == -900

    def test_negative_large_minimum(self):
        result = self.normalizer.smart_minimum(-947)
        assert result == -1000

    def test_negative_float_maximum(self):
        result = self.normalizer.smart_maximum(-3.5)
        assert result == -3.0

    def test_negative_float_minimum(self):
        result = self.normalizer.smart_minimum(-3.5)
        assert result == -4.0


class TestPadding:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_maximum_with_padding(self):
        result = self.normalizer.smart_maximum(900, padding=0.1)
        assert result == 1000

    def test_minimum_with_padding(self):
        result = self.normalizer.smart_minimum(1000, padding=0.1)
        assert result == 900

    def test_zero_padding_is_default(self):
        assert self.normalizer.smart_maximum(947) == self.normalizer.smart_maximum(947, padding=0.0)


class TestNormalizeBoundsTreeWalk:
    def setup_method(self):
        self.normalizer = BoundNormalizer()

    def test_normalizes_integer_node(self):
        node = SchemaNode(type=SchemaType.INTEGER, minimum=23, maximum=947)
        self.normalizer.normalize_bounds(node)
        assert node.minimum == 20
        assert node.maximum == 1000

    def test_normalizes_number_node(self):
        node = SchemaNode(type=SchemaType.NUMBER, minimum=0.0037, maximum=947.5)
        self.normalizer.normalize_bounds(node)
        assert node.minimum == 0.003
        assert node.maximum == 1000.0

    def test_walks_object_properties(self):
        node = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "age": SchemaNode(type=SchemaType.INTEGER, minimum=5, maximum=73),
                "name": SchemaNode(type=SchemaType.STRING, maxLength=10),
            },
        )
        self.normalizer.normalize_bounds(node)
        age = node.properties["age"]
        assert isinstance(age, SchemaNode)
        assert age.minimum == 5
        assert age.maximum == 80

    def test_walks_array_items(self):
        node = SchemaNode(
            type=SchemaType.ARRAY,
            items=SchemaNode(type=SchemaType.INTEGER, minimum=15, maximum=947),
        )
        self.normalizer.normalize_bounds(node)
        items = node.items
        assert isinstance(items, SchemaNode)
        assert items.minimum == 15
        assert items.maximum == 1000

    def test_walks_anyof_variants(self):
        node = SchemaNode(
            anyOf=[
                SchemaNode(type=SchemaType.INTEGER, minimum=5, maximum=73),
                SchemaNode(type=SchemaType.NUMBER, minimum=0.5, maximum=150.0),
            ]
        )
        self.normalizer.normalize_bounds(node)
        int_variant = node.anyOf[0]
        num_variant = node.anyOf[1]
        assert isinstance(int_variant, SchemaNode)
        assert isinstance(num_variant, SchemaNode)
        assert int_variant.maximum == 80
        assert num_variant.maximum == 200.0

    def test_does_not_affect_string_nodes(self):
        node = SchemaNode(type=SchemaType.STRING, minLength=3, maxLength=50)
        self.normalizer.normalize_bounds(node)
        assert node.minLength == 3
        assert node.maxLength == 50

    def test_deeply_nested_normalization(self):
        node = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "data": SchemaNode(
                    type=SchemaType.OBJECT,
                    properties={
                        "value": SchemaNode(type=SchemaType.INTEGER, minimum=23, maximum=947),
                    },
                ),
            },
        )
        self.normalizer.normalize_bounds(node)
        value_node = node.properties["data"].properties["value"]
        assert isinstance(value_node, SchemaNode)
        assert value_node.minimum == 20
        assert value_node.maximum == 1000
