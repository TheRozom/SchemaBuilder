from src.shared.models import SchemaNode, SchemaType


class RegexInjector:
    def inject(
        self, schema: SchemaNode, target_path: str, regex: str, current_path: str = ""
    ):
        if current_path == target_path and schema.type == SchemaType.STRING:
            schema.pattern = regex
            return

        if schema.type == SchemaType.OBJECT:
            for k, v in schema.properties.items():
                next_path = f"{current_path}.{k}" if current_path else k
                if target_path.startswith(next_path):
                    if isinstance(v, SchemaNode):
                        self.inject(v, target_path, regex, next_path)
                    else:
                        # Convert dict to SchemaNode and update the original properties
                        prop_schema = SchemaNode(**v)
                        self.inject(prop_schema, target_path, regex, next_path)
                        schema.properties[k] = prop_schema

        if schema.type == SchemaType.ARRAY and schema.items:
            next_path = current_path + "[]"
            if target_path.startswith(next_path):
                if isinstance(schema.items, SchemaNode):
                    self.inject(schema.items, target_path, regex, next_path)
                else:
                    # Convert dict to SchemaNode and update the original items
                    items_schema = SchemaNode(**schema.items)
                    self.inject(items_schema, target_path, regex, next_path)
                    schema.items = items_schema
