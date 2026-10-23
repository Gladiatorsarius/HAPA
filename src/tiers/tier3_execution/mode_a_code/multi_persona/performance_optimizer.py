"""Performance-focused code review persona."""

from src.core.schemas import ReviewPersona

from ._base import PersonaReviewer


class PerformanceOptimizer(PersonaReviewer):
    persona = ReviewPersona.PERFORMANCE_OPTIMIZER
    focus = "performance optimizer"


__all__ = ["PerformanceOptimizer"]
