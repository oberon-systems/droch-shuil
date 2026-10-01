import hashlib

from pydantic_core import core_schema


class Secret(str):
    """Plaintext inside the model, sha256:<hex> in the public view."""

    def digest(self) -> str:
        return 'sha256:' + hashlib.sha256(self.encode()).hexdigest()

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        # A union tries its members strictly first, and there only a value
        # that arrived as a Secret is one; a field of its own takes any string.
        return core_schema.lax_or_strict_schema(
            lax_schema=core_schema.no_info_after_validator_function(cls, core_schema.str_schema()),
            strict_schema=core_schema.is_instance_schema(cls),
            serialization=core_schema.plain_serializer_function_ser_schema(cls._dump, info_arg=True),
        )

    @staticmethod
    def _dump(value, info):
        if not isinstance(value, Secret):
            return value

        public = (info.context or {}).get('public')

        return value.digest() if public and value else str(value)
