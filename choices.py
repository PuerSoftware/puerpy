import inspect

from enum      import Enum, EnumMeta
from typing    import Generator, Any


class ChoicesMeta(EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        new_cls      = super().__new__(metacls, cls, bases, classdict)
        new_cls.enum = Enum(f'{cls}_Enum', {
            name: value
            for name, value in new_cls.fields(idx=0)
        })
        return new_cls


class Choices(metaclass=ChoicesMeta):
    @classmethod
    def _is_attr(cls, name: str, value: Any) -> bool:
        return (
            name != 'enum'                and
            not name.startswith('_')      and
            not name.startswith('__')     and
            not inspect.isfunction(value) and
            not inspect.isroutine(value)
        )

    @classmethod
    def fields(cls, slice: list | tuple = None, idx: int = None) -> Generator:
        attributes = (
            (name, value._value_)
                for name, value in vars(cls).items() if cls._is_attr(name, value)
        )
        if slice is not None:
            return (
                (name, value[slice[0]:slice[1]])
                    for name, value in attributes
            )
        if idx is not None:
            return (
                (name, value[idx])
                for name, value in attributes
            )
        return attributes
    
"""
Example usage
----------------------------------
from puerpy.choices import Choices


class Fruits(Choices):
    APPLE  = 1, 'apple'
    ORANGE = 2, 'orange'
    CHERRY = 3, 'cherry'

Fruits
Fruits.APPLE
Fruits.enum
Fruits.enum.APPLE

list(Fruits.fields())
list(Fruits.fields(idx=1))
list(Fruits.fields(slice=[0,1]))
---------------------------------
<enum 'Fruits'>
<Fruits.APPLE: (1, 'apple')>
<enum 'Fruits_Enum'>
<Fruits_Enum.APPLE: 1>

[('APPLE', (1, 'apple')), ('ORANGE', (2, 'orange')), ('CHERRY', (3, 'cherry'))]
[('APPLE', 'apple'), ('ORANGE', 'orange'), ('CHERRY', 'cherry')]
[('APPLE', (1,)), ('ORANGE', (2,)), ('CHERRY', (3,))]
"""
