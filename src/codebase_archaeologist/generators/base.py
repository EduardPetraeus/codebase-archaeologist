"""Base class for all generators."""

from abc import ABC, abstractmethod

from codebase_archaeologist.models import CodebaseProfile


class BaseGenerator(ABC):
    """Abstract base for document generators."""

    def __init__(self, profile: CodebaseProfile):
        self.profile = profile

    @abstractmethod
    def generate(self) -> str:
        """Generate markdown document content."""
