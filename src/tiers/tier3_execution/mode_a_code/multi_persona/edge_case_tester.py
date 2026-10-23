"""Edge-case-focused code review persona."""

from src.core.schemas import ReviewPersona

from ._base import PersonaReviewer


class EdgeCaseTester(PersonaReviewer):
    persona = ReviewPersona.EDGE_CASE_TESTER
    focus = "edge-case tester"


__all__ = ["EdgeCaseTester"]
