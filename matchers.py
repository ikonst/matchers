"""
This module extends the idea behind unittest.mock.ANY with a "conditional ANY".

For example, it allows comparing API responses with higher fidelity:
```
client.get_object() == {
    "id": AnyInteger(),
    "name": AnyString(),
}
```

It also allows extracting data for additional testing. For example, this code:
```
do_something.assert_called_once_with(ANY)
_, args, kwargs in do_something.mock_calls[0]
assert args[0].startswith('prefix')
```
can be replaced with:
```
prefix_attr = AnyString()
do_something.assert_called_once_with(prefix_attr)
assert prefix_attr.actual.startswith('prefix')
```
"""
import re
from typing import Any, Callable, Iterable, Optional

_not_compared = object()
_not_matched = object()


class AnyIf:
    """
    Similar to mock.ANY, this is a chameleon object that matches any object as long as a condition holds.
    """

    def __init__(self, validator: Optional[Callable[[Any], bool]] = None) -> None:
        self.description = super().__repr__()
        self.validator = validator
        self.actual = _not_matched
        self.actuals = []

    @property
    def compared(self) -> bool:
        return self.actual is not _not_compared

    @property
    def matched(self) -> bool:
        return self.actual is not _not_compared and self.actual is not _not_matched

    def _validator(self, other: Any) -> bool:
        return not self.validator or self.validator(other)

    def __eq__(self, other: Any) -> bool:
        res = self._validator(other)
        if res:
            self.actual = other
            self.actuals.append(other)
        else:
            self.actual = _not_matched
        return res

    def __ne__(self, other: Any) -> bool:
        return not (self == other)

    def __repr__(self) -> str:
        """Returns the last compared value as the representation, to allow for smoother diffs."""
        if not self.compared:
            return f'<not compared: {self.description}>'
        elif not self.matched:
            return self.description
        else:
            return repr(self.actual)


class AnyInteger(AnyIf):
    def __init__(self) -> None:
        super().__init__(lambda v: isinstance(v, int))


class AnyString(AnyIf):
    def __init__(self) -> None:
        super().__init__(lambda v: isinstance(v, str))


class AnyUUID(AnyIf):
    def _validator(self, other: Any) -> bool:
        from uuid import UUID
        if not isinstance(other, (str, UUID)):
            return False
        try:
            UUID(other)
            return True
        except ValueError:
            return False


class AnyStringMatchingRegex(AnyIf):
    def __init__(self, pattern: str) -> None:
        pattern = re.compile(pattern, re.DOTALL)
        super().__init__(lambda v: (pattern.match(v) is not None))
        self.other = pattern


class Unordered(AnyIf):
    def __init__(self, items: Iterable) -> None:
        super().__init__(lambda v: sorted(v) == sorted(items))


class AnyOf(AnyIf):
    def __init__(self, *items: Iterable) -> None:
        super().__init__(lambda v: v in items)
        self.description = f"any of {items}"


class AnyWebURLString(AnyIf):
    def __init__(self) -> None:
        super().__init__(lambda v: isinstance(v, str) and (v.startswith('http://') or v.startswith('https://')))
