from typing import Any, Dict, Union

from src.shared.models import SchemaNode, SchemaType, SchemaKeyword


class SchemaMerger:

    def merge(self, first_schema: SchemaNode, second_schema: SchemaNode) -> SchemaNode:
        first_options = (
            list(first_schema.anyOf) if first_schema.anyOf else [first_schema]
        )
        second_options = (
            list(second_schema.anyOf) if second_schema.anyOf else [second_schema]
        )

        for second_option in second_options:
            was_merged = False
            for index, first_option in enumerate(first_options):
                first_type = (
                    first_option.type
                    if isinstance(first_option, SchemaNode)
                    else first_option.get(SchemaKeyword.TYPE)
                )
                second_type = (
                    second_option.type
                    if isinstance(second_option, SchemaNode)
                    else second_option.get(SchemaKeyword.TYPE)
                )

                if first_type == second_type or {first_type, second_type} == {
                    SchemaType.INTEGER,
                    SchemaType.NUMBER,
                }:
                    first_options[index] = self._merge_same_type(
                        first_option, second_option
                    )
                    was_merged = True
                    break

            if not was_merged:
                first_options.append(second_option)

        if len(first_options) == 1:
            return (
                first_options[0]
                if isinstance(first_options[0], SchemaNode)
                else SchemaNode(**first_options[0])
            )
        return SchemaNode(anyOf=first_options)

    def _merge_same_type(
        self,
        first_schema: Union[SchemaNode, Dict[str, Any]],
        second_schema: Union[SchemaNode, Dict[str, Any]],
    ) -> SchemaNode:
        first_node = (
            first_schema
            if isinstance(first_schema, SchemaNode)
            else SchemaNode(**first_schema)
        )
        second_node = (
            second_schema
            if isinstance(second_schema, SchemaNode)
            else SchemaNode(**second_schema)
        )

        first_type = first_node.type
        second_type = second_node.type

        if first_type != second_type and {first_type, second_type} == {
            SchemaType.INTEGER,
            SchemaType.NUMBER,
        }:
            return SchemaNode(type=SchemaType.NUMBER, minimum=0)

        if first_type == SchemaType.STRING:
            return self._merge_string(first_node, second_node)

        if first_type == SchemaType.INTEGER:
            return self._merge_integer(first_node, second_node)

        if first_type == SchemaType.OBJECT:
            return self._merge_object(first_node, second_node)

        if first_type == SchemaType.ARRAY:
            return self._merge_array(first_node, second_node)

        return first_node

    def _merge_string(
        self, first_schema: SchemaNode, second_schema: SchemaNode
    ) -> SchemaNode:
        first_max_length = first_schema.maxLength or 0
        second_max_length = second_schema.maxLength or 0

        merged_schema = SchemaNode(
            type=SchemaType.STRING,
            minLength=0,
            maxLength=max(first_max_length, second_max_length),
        )

        first_pattern = first_schema.pattern
        second_pattern = second_schema.pattern
        if first_pattern == second_pattern and first_pattern:
            merged_schema.pattern = first_pattern
        return merged_schema

    def _merge_integer(
        self, first_schema: SchemaNode, second_schema: SchemaNode
    ) -> SchemaNode:
        first_maximum = first_schema.maximum or 0
        second_maximum = second_schema.maximum or 0
        return SchemaNode(
            type=SchemaType.INTEGER,
            minimum=0,
            maximum=max(first_maximum, second_maximum),
        )

    def _merge_object(
        self, first_schema: SchemaNode, second_schema: SchemaNode
    ) -> SchemaNode:
        first_properties = first_schema.properties
        second_properties = second_schema.properties

        all_property_keys = set(first_properties.keys()) | set(second_properties.keys())
        merged_properties = {}
        for property_key in all_property_keys:
            if property_key in first_properties and property_key in second_properties:
                first_property = (
                    first_properties[property_key]
                    if isinstance(first_properties[property_key], SchemaNode)
                    else SchemaNode(**first_properties[property_key])
                )
                second_property = (
                    second_properties[property_key]
                    if isinstance(second_properties[property_key], SchemaNode)
                    else SchemaNode(**second_properties[property_key])
                )
                merged_properties[property_key] = self.merge(
                    first_property, second_property
                )
            elif property_key in first_properties:
                merged_properties[property_key] = first_properties[property_key]
            else:
                merged_properties[property_key] = second_properties[property_key]

        return SchemaNode(
            type=SchemaType.OBJECT,
            properties=merged_properties,
            additionalProperties=False,
        )

    def _merge_array(
        self, first_schema: SchemaNode, second_schema: SchemaNode
    ) -> SchemaNode:
        first_items = first_schema.items
        second_items = second_schema.items
        first_max_items = first_schema.maxItems or 0
        second_max_items = second_schema.maxItems or 0

        first_items_node = (
            first_items
            if isinstance(first_items, SchemaNode)
            else SchemaNode(**first_items) if first_items else SchemaNode()
        )
        second_items_node = (
            second_items
            if isinstance(second_items, SchemaNode)
            else SchemaNode(**second_items) if second_items else SchemaNode()
        )

        return SchemaNode(
            type=SchemaType.ARRAY,
            items=self.merge(first_items_node, second_items_node),
            minItems=0,
            maxItems=max(first_max_items, second_max_items),
        )
