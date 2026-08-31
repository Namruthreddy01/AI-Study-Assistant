class StudyAssistantError(Exception):
    """Expected domain error that can be safely shown to a student."""


class InvalidDocumentError(StudyAssistantError):
    """The uploaded file is not a usable PDF."""


class NotFoundError(StudyAssistantError):
    """The requested resource does not exist."""


class GenerationError(StudyAssistantError):
    """The configured AI provider did not return a usable response."""

