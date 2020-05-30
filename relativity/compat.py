"""
This module exists for backwards-compatibility.
"""
import warnings

from django.db.models import F, Q

__all__ = ("F", "Q")

warnings.warn(
    "relativity.compat is deprecated. Please update all usages of Q and F to use the equivalents from django.db.models.",
    DeprecationWarning,
)
