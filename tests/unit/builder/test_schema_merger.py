from src.bl.builder.mergers import SchemaMerger
from src.shared.models import SchemaNode, SchemaType


class TestSchemaMergerStrings:
    def test_merge_two_strings_maxlength_takes_max(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING, maxLength=10)
        second = SchemaNode(type=SchemaType.STRING, maxLength=20)
        result = merger.merge(first, second)
        assert result.type == SchemaType.STRING
        assert result.maxLength == 20

    def test_merge_strings_with_same_pattern_preserves_pattern(self):
        merger = SchemaMerger()
        pattern = r"^[a-z]+$"
        first = SchemaNode(type=SchemaType.STRING, maxLength=10, pattern=pattern)

        second = SchemaNode(type=SchemaType.STRING, maxLength=15, pattern=pattern)

        result = merger.merge(first, second)
        assert result.type == SchemaType.STRING
        assert result.pattern == pattern
        assert result.maxLength == 15

    def test_merge_strings_with_different_patterns_drops_pattern(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING, maxLength=10, pattern=r"^[a-z]+$")

        second = SchemaNode(type=SchemaType.STRING, maxLength=15, pattern=r"^\d+$")

        result = merger.merge(first, second)
        assert result.type == SchemaType.STRING
        assert result.pattern is None
        assert result.maxLength == 15

    def test_merge_strings_one_with_pattern_one_without_drops_pattern(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING, maxLength=10, pattern=r"^[a-z]+$")

        second = SchemaNode(type=SchemaType.STRING, maxLength=15)
        result = merger.merge(first, second)
        assert result.type == SchemaType.STRING
        assert result.pattern is None


class TestSchemaMergerIntegers:
    def test_merge_two_integers_maximum_takes_max(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.INTEGER, maximum=50)
        second = SchemaNode(type=SchemaType.INTEGER, maximum=100)
        result = merger.merge(first, second)
        assert result.type == SchemaType.INTEGER
        assert result.maximum == 100

    def test_merge_two_integers_with_minimum_takes_min(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.INTEGER, minimum=5, maximum=50)
        second = SchemaNode(type=SchemaType.INTEGER, minimum=10, maximum=100)
        result = merger.merge(first, second)
        assert result.type == SchemaType.INTEGER
        assert result.minimum == 5

    def test_merge_integer_and_number_becomes_number(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.INTEGER, maximum=50)
        second = SchemaNode(type=SchemaType.NUMBER, maximum=100)
        result = merger.merge(first, second)
        assert result.type == SchemaType.NUMBER
        assert result.minimum == 0

    def test_merge_number_and_integer_becomes_number(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.NUMBER, maximum=100)
        second = SchemaNode(type=SchemaType.INTEGER, maximum=50)
        result = merger.merge(first, second)
        assert result.type == SchemaType.NUMBER


class TestSchemaMergerObjects:
    def test_merge_two_objects_with_same_properties(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "name": SchemaNode(type=SchemaType.STRING, maxLength=10),
                "age": SchemaNode(type=SchemaType.INTEGER, maximum=50),
            },
        )
        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "name": SchemaNode(type=SchemaType.STRING, maxLength=20),
                "age": SchemaNode(type=SchemaType.INTEGER, maximum=100),
            },
        )
        result = merger.merge(first, second)
        assert result.type == SchemaType.OBJECT
        assert "name" in result.properties
        assert "age" in result.properties
        name_prop = result.properties["name"]
        assert isinstance(name_prop, SchemaNode)
        assert name_prop.maxLength == 20
        age_prop = result.properties["age"]
        assert isinstance(age_prop, SchemaNode)
        assert age_prop.maximum == 100

    def test_merge_two_objects_with_different_properties(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "name": SchemaNode(type=SchemaType.STRING, maxLength=10),
            },
        )
        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "email": SchemaNode(type=SchemaType.STRING, maxLength=50),
            },
        )
        result = merger.merge(first, second)
        assert result.type == SchemaType.OBJECT
        assert "name" in result.properties
        assert "email" in result.properties

    def test_merge_objects_with_overlapping_properties_recursive_merge(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "name": SchemaNode(type=SchemaType.STRING, maxLength=10),
                "address": SchemaNode(
                    type=SchemaType.OBJECT,
                    properties={
                        "city": SchemaNode(type=SchemaType.STRING, maxLength=20),
                    },
                ),
            },
        )

        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "age": SchemaNode(type=SchemaType.INTEGER, maximum=100),
                "address": SchemaNode(
                    type=SchemaType.OBJECT,
                    properties={
                        "city": SchemaNode(type=SchemaType.STRING, maxLength=30),
                        "zip": SchemaNode(type=SchemaType.STRING, maxLength=10),
                    },
                ),
            },
        )

        result = merger.merge(first, second)
        assert result.type == SchemaType.OBJECT
        assert "name" in result.properties
        assert "age" in result.properties
        assert "address" in result.properties
        address = result.properties["address"]
        assert isinstance(address, SchemaNode)
        assert "city" in address.properties
        assert "zip" in address.properties
        city = address.properties["city"]
        assert isinstance(city, SchemaNode)
        assert city.maxLength == 30


class TestSchemaMergerArrays:
    def test_merge_two_arrays_items_merged_maxitems_is_max(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.ARRAY,
            items=SchemaNode(type=SchemaType.STRING, maxLength=10),
            maxItems=5,
        )
        second = SchemaNode(
            type=SchemaType.ARRAY,
            items=SchemaNode(type=SchemaType.STRING, maxLength=20),
            maxItems=10,
        )
        result = merger.merge(first, second)
        assert result.type == SchemaType.ARRAY
        assert result.maxItems == 10
        assert result.minItems == 0
        items = result.items
        assert isinstance(items, SchemaNode)
        assert items.maxLength == 20

    def test_merge_arrays_with_different_item_types_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.ARRAY,
            items=SchemaNode(type=SchemaType.STRING, maxLength=10),
            maxItems=5,
        )
        second = SchemaNode(
            type=SchemaType.ARRAY,
            items=SchemaNode(type=SchemaType.INTEGER, maximum=100),
            maxItems=10,
        )
        result = merger.merge(first, second)
        assert result.type == SchemaType.ARRAY
        assert result.maxItems == 10
        items = result.items
        assert isinstance(items, SchemaNode)
        assert items.anyOf is not None
        assert len(items.anyOf) == 2


class TestSchemaMergerDifferentTypes:
    def test_merge_different_types_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING, maxLength=10)
        second = SchemaNode(type=SchemaType.BOOLEAN)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2
        types = set()

        for option in result.anyOf:
            if isinstance(option, SchemaNode):
                types.add(option.type)

            else:
                types.add(option.get("type"))

        assert SchemaType.STRING in types
        assert SchemaType.BOOLEAN in types

    def test_merge_with_existing_anyof_extends_options(self):
        merger = SchemaMerger()
        first = SchemaNode(
            anyOf=[
                SchemaNode(type=SchemaType.STRING, maxLength=10),
                SchemaNode(type=SchemaType.INTEGER, maximum=50),
            ]
        )
        second = SchemaNode(type=SchemaType.BOOLEAN)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 3
        types = set()

        for option in result.anyOf:
            if isinstance(option, SchemaNode):
                types.add(option.type)

            else:
                types.add(option.get("type"))

        assert SchemaType.STRING in types
        assert SchemaType.INTEGER in types
        assert SchemaType.BOOLEAN in types

    def test_merge_anyof_with_matching_type_merges_instead_of_extending(self):
        merger = SchemaMerger()
        first = SchemaNode(
            anyOf=[
                SchemaNode(type=SchemaType.STRING, maxLength=10),
                SchemaNode(type=SchemaType.INTEGER, maximum=50),
            ]
        )
        second = SchemaNode(type=SchemaType.STRING, maxLength=20)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2
        string_option = None

        for option in result.anyOf:
            if isinstance(option, SchemaNode) and option.type == SchemaType.STRING:
                string_option = option
                break

        assert string_option is not None
        assert string_option.maxLength == 20


class TestSchemaMergerNull:
    def test_merge_null_with_string_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.NULL)
        second = SchemaNode(type=SchemaType.STRING, maxLength=10)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2

    def test_merge_null_with_integer_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.NULL)
        second = SchemaNode(type=SchemaType.INTEGER, maximum=100)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2

    def test_merge_null_with_object_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.NULL)
        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={"name": SchemaNode(type=SchemaType.STRING)},
        )
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2


class TestSchemaMergerBoolean:
    def test_merge_boolean_with_string_creates_anyof(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.BOOLEAN)
        second = SchemaNode(type=SchemaType.STRING, maxLength=10)
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 2
        types = set()

        for option in result.anyOf:
            if isinstance(option, SchemaNode):
                types.add(option.type)

            else:
                types.add(option.get("type"))

        assert SchemaType.BOOLEAN in types
        assert SchemaType.STRING in types

    def test_merge_two_booleans_returns_boolean(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.BOOLEAN)
        second = SchemaNode(type=SchemaType.BOOLEAN)
        result = merger.merge(first, second)
        assert result.type == SchemaType.BOOLEAN
        assert not result.anyOf


class TestSchemaMergerEdgeCases:
    def test_merge_with_none_maxlength_uses_other(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING)
        second = SchemaNode(type=SchemaType.STRING, maxLength=20)
        result = merger.merge(first, second)
        assert result.maxLength == 20

    def test_merge_with_both_none_maxlength_uses_zero(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.STRING)
        second = SchemaNode(type=SchemaType.STRING)
        result = merger.merge(first, second)
        assert result.maxLength == 0

    def test_merge_with_none_maximum_uses_other(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.INTEGER)
        second = SchemaNode(type=SchemaType.INTEGER, maximum=100)
        result = merger.merge(first, second)
        assert result.maximum == 100

    def test_merge_arrays_with_none_items(self):
        merger = SchemaMerger()
        first = SchemaNode(type=SchemaType.ARRAY, maxItems=5)
        second = SchemaNode(type=SchemaType.ARRAY, maxItems=10)
        result = merger.merge(first, second)
        assert result.type == SchemaType.ARRAY
        assert result.maxItems == 10

    def test_merge_objects_sets_additional_properties_false(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.OBJECT,
            properties={"name": SchemaNode(type=SchemaType.STRING)},
        )
        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={"age": SchemaNode(type=SchemaType.INTEGER)},
        )
        result = merger.merge(first, second)
        assert result.additionalProperties is False

    def test_merge_two_anyof_schemas(self):
        merger = SchemaMerger()
        first = SchemaNode(
            anyOf=[
                SchemaNode(type=SchemaType.STRING, maxLength=10),
                SchemaNode(type=SchemaType.INTEGER, maximum=50),
            ]
        )
        second = SchemaNode(
            anyOf=[
                SchemaNode(type=SchemaType.BOOLEAN),
                SchemaNode(type=SchemaType.NULL),
            ]
        )
        result = merger.merge(first, second)
        assert result.anyOf is not None
        assert len(result.anyOf) == 4

    def test_merge_complex_nested_objects(self):
        merger = SchemaMerger()
        first = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "user": SchemaNode(
                    type=SchemaType.OBJECT,
                    properties={
                        "profile": SchemaNode(
                            type=SchemaType.OBJECT,
                            properties={
                                "name": SchemaNode(type=SchemaType.STRING, maxLength=10),
                            },
                        ),
                    },
                ),
            },
        )
        second = SchemaNode(
            type=SchemaType.OBJECT,
            properties={
                "user": SchemaNode(
                    type=SchemaType.OBJECT,
                    properties={
                        "profile": SchemaNode(
                            type=SchemaType.OBJECT,
                            properties={
                                "name": SchemaNode(type=SchemaType.STRING, maxLength=20),
                                "bio": SchemaNode(type=SchemaType.STRING, maxLength=100),
                            },
                        ),
                    },
                ),
            },
        )
        result = merger.merge(first, second)
        user = result.properties["user"]
        assert isinstance(user, SchemaNode)
        profile = user.properties["profile"]
        assert isinstance(profile, SchemaNode)
        assert "name" in profile.properties
        assert "bio" in profile.properties
        name = profile.properties["name"]
        assert isinstance(name, SchemaNode)
        assert name.maxLength == 20
