from mongoengine.fields import BaseField
from enum import Enum, auto

class EnumField(BaseField):
    def __init__(self, enum: Enum, *args, **kwargs):
        self.enum = enum
        # print("init", enum)
        kwargs['choices'] = [e.value for e in enum]
        super(EnumField, self).__init__( *args, **kwargs)

    def __get_enum_value(self, enum):
        # print("getting value", enum.value)
        return enum.value

    def __get_enum_tuple(self, enum):
        return (enum.name, enum.value)

    def to_mongo(self, value):
        # print("Enum to mongo:", self.__get_enum_value(value))
        return self.__get_enum_value(value)

    def to_python(self, value):
        enum_value = super(EnumField, self).to_python(value)
        # print("Enum to python:", self.enum(enum_value))
        return self.enum(enum_value)

    def prepare_query_value(self, op, value):
        return super(EnumField, self).prepare_query_value(
            op, self.__get_enum_value(value))

    #Todo:
    # Understand why 'validate' is not used in BaseField (instead / on top of _validate).
    # def validate(self, value, clean=True):
    #     print ("Validation: got", value)
    #     test_value = self.__get_enum_value(value) if isinstance(value, self.enum) else value
    #     return super(EnumField, self).validate(test_value)

    def _validate(self, value, **kwargs):
        return super(EnumField, self)._validate(self.__get_enum_value(value), **kwargs)
