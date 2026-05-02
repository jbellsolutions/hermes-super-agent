"""Langfuse trace decorator. TODO(stage-5): wire langfuse SDK."""
from __future__ import annotations

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


def trace(name: str | None = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def deco(fn: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # TODO(stage-5): start Langfuse span, capture inputs/outputs/cost
            return fn(*args, **kwargs)
        return wrapper
    return deco
