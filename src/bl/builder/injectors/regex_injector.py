from src.shared.models import SchemaNode, SchemaType


class RegexInjector:
    def inject(self, schema: SchemaNode, target_path: str, regex: str, current_path: str = ""):
        if current_path == target_path and schema.type == SchemaType.STRING:
            schema.pattern = regex
            return

        if schema.type == SchemaType.OBJECT:
            for k, v in schema.properties.items():
                next_path = f"{current_path}.{k}" if current_path else k
                if target_path.startswith(next_path):
                    prop_schema = v if isinstance(v, SchemaNode) else SchemaNode(**v)
                    self.inject(prop_schema, target_path, regex, next_path)

        if schema.type == SchemaType.ARRAY and schema.items:
            next_path = current_path + "[]"
            if target_path.startswith(next_path):
                items_schema = schema.items if isinstance(schema.items, SchemaNode) else SchemaNode(**schema.items)
                self.inject(items_schema, target_path, regex, next_path)
