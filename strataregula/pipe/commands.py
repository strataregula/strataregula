"""
Base command infrastructure for pipeline processing.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Base class for all pipeline commands."""

    name: str = ""
    description: str = ""
    category: str = "general"
    input_types: List[str] = []
    output_types: List[str] = []

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Execute the command with given data."""
        pass

    def validate_input(self, data: Any) -> bool:
        """Validate input data type."""
        if not self.input_types:
            return True

        data_type = type(data).__name__
        return data_type in self.input_types or "Any" in self.input_types

    def get_metadata(self) -> Dict[str, Any]:
        """Get command metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "input_types": self.input_types,
            "output_types": self.output_types
        }
