from typing import Callable, List

import re
import typeguard
import valid8


validate = valid8.validate


@typeguard.typechecked
def pattern(regex: str) -> Callable[[str], bool]:
    r = re.compile(regex)

    def res(value):
        return bool(r.fullmatch(value))

    res.__name__ = f'pattern({regex})'
    return res


def does_not_has_attributes(cls, attributes: List[str], and_annotations: bool = False):
    if and_annotations:
        validate(
            f"{cls.__name__} has no attribute __annotations__",
            hasattr(cls, '__annotations__') and cls.__annotations__ != {},
            equals=False
        )
    for attribute in attributes:
        validate(f"{cls.__name__} has no attribute {attribute}", hasattr(cls, attribute), equals=False)
