from mongoengine.fields import BaseField
from enum import Enum, auto

class EnumField(BaseField):
    def __init__(self, enum: Enum, *args, **kwargs):
        self.enum = enum
        kwargs['choices'] = [e.value for e in enum]
        super(EnumField, self).__init__( *args, **kwargs)

    def __get_enum_value(self, enum):
        return enum.value

    def to_mongo(self, value):
        return self.__get_enum_value(value)

    def to_python(self, value):
        enum_value = super(EnumField, self).to_python(value)
        return self.enum(enum_value)

    def prepare_query_value(self, op, value):
        return super(EnumField, self).prepare_query_value(
            op, self.__get_enum_value(value))

    def _validate(self, value, **kwargs):
        return super(EnumField, self)._validate(self.__get_enum_value(value), **kwargs)
