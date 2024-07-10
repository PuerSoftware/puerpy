from typing      import Any
from dataclasses import fields
from betterproto import Message


class Proto:
    @staticmethod
    def serialize(data: dict[str, Any], _type: Message) -> Message:
        serialized_data = {}
        for field in fields(_type):
            value = data.get(field.name)
            if value:
                if isinstance(field.type, type) and issubclass(field.type, bool):
                    serialized_data[field.name] = bool(value)
                elif isinstance(field.type, type) and issubclass(field.type, int):
                    serialized_data[field.name] = int(value)
                elif isinstance(field.type, type) and issubclass(field.type, float):
                    serialized_data[field.name] = float(value)
                elif isinstance(field.type, type) and issubclass(field.type, str):
                    serialized_data[field.name] = str(value)
                elif isinstance(field.type, type) and issubclass(field.type, bytes):
                    if hasattr(value, 'bytes'):
                        serialized_data[field.name] = value.bytes
                    else:
                        serialized_data[field.name] = bytes(value)
                else:
                    serialized_data[field.name] = value
        return _type(**serialized_data)
        