import dataclasses
from dataclasses import InitVar
from typing import Optional

import typeguard

from dumbo_esse3.utils import validators
from dumbo_esse3.utils.validators import validate


def _arithmetic(cls):
    validate(cls.__name__, hasattr(cls, '__add__'), equals=False)
    validate(cls.__name__, hasattr(cls, '__mul__'), equals=False)
    validate(cls.__name__, hasattr(cls, '__rmul__'), equals=False)
    validate(cls.__name__, hasattr(cls, '__neg__'), equals=False)
    setattr(cls, '__add__', lambda self, other: cls(self.value + (other.value if type(other) == cls else other)))
    setattr(cls, '__mul__', lambda self, other: cls(self.value * (other.value if type(other) == cls else other)))
    setattr(cls, '__rmul__', lambda self, other: cls(self.value * (other.value if type(other) == cls else other)))
    setattr(cls, '__neg__', lambda self: getattr(cls, '__mul__')(-1))


@typeguard.typechecked
def bounded_integer(min_value: int, max_value: int):
    validate('min_value', min_value, max_value=max_value)

    def decorator(cls):
        validators.does_not_has_attributes(cls, [
            '__int__',
            'min_value',
            'max_value',
            'parse',
            'of',
            '__post_init__',
            'toJSON',
        ], and_annotations=True)

        cls.__annotations__ = {'value': int}

        if getattr(cls, '__str__') == getattr(object, '__str__'):
            setattr(cls, '__str__', lambda self: str(self.value))

        setattr(cls, '__int__', lambda self: self.value)
        setattr(cls, 'min_value', staticmethod(lambda: min_value))
        setattr(cls, 'max_value', staticmethod(lambda: max_value))
        setattr(cls, 'parse', staticmethod(lambda s: cls(int(s))))
        setattr(cls, 'of', staticmethod(lambda s: cls(int(s))))

        if not hasattr(cls, '_validate'):
            setattr(cls, '_validate', lambda self: None)

        def post_init(self):
            validate('value', self.value, min_value=self.min_value(), max_value=self.max_value())
            self._validate()

        setattr(cls, '__post_init__', post_init)
        setattr(cls, 'toJSON', lambda self: self.value)
        setattr(cls, '__format__', lambda self, format_spec: self.value.__format__(format_spec))

        _arithmetic(cls)

        return dataclasses.dataclass(frozen=True, order=True)(cls)

    return decorator


@typeguard.typechecked
def bounded_string(min_length: int, max_length: int, pattern: str = r'.*', private_init: Optional[bool] = False):
    validate('min_length', min_length, min_value=0, max_value=max_length)
    validate('max_length', max_length, min_value=min_length)

    def decorator(cls):
        validators.does_not_has_attributes(cls, [
            'min_length',
            'max_length',
            'pattern',
            'parse',
            'of',
            'toJSON',
            '__post_init__',
        ], and_annotations=True)

        cls.__annotations__ = {'value': str}

        if getattr(cls, '__str__') == getattr(object, '__str__'):
            setattr(cls, '__str__', lambda self: self.value)

        setattr(cls, 'min_length', staticmethod(lambda: min_length))
        setattr(cls, 'max_length', staticmethod(lambda: max_length))
        setattr(cls, 'pattern', staticmethod(lambda: pattern))
        setattr(cls, 'parse', staticmethod(lambda s: cls(s)))
        setattr(cls, 'of', staticmethod(lambda s: cls(s)))
        setattr(cls, 'toJSON', lambda self: self.value)

        if pattern == r'.*':
            def __validate(self):
                validate('value', self.value, min_len=self.min_length(), max_len=self.max_length())
        else:
            def __validate(self):
                validate('value', self.value, min_len=self.min_length(), max_len=self.max_length(),
                         custom=validators.pattern(self.pattern()))

        if not hasattr(cls, '_validate'):
            setattr(cls, '_validate', lambda self: None)

        if private_init:
            validate('cls', hasattr(cls, '_validate_init_key'), equals=True)
            cls.__annotations__['init_key'] = InitVar

            def post_init(self, init_key):
                self._validate_init_key(init_key)
                __validate(self)
                self._validate()
        else:
            def post_init(self):
                __validate(self)
                self._validate()
        setattr(cls, '__post_init__', post_init)

        return dataclasses.dataclass(frozen=True, order=True)(cls)

    return decorator
