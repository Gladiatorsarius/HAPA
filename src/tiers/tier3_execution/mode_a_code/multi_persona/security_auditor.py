"""Security-focused code review persona."""

from src.core.schemas import ReviewPersona

from ._base import PersonaReviewer


class SecurityAuditor(PersonaReviewer):
    persona = ReviewPersona.SECURITY_AUDITOR
    focus = "security auditor"


__all__ = ["SecurityAuditor"]
