"""
Base command interface for StrataRegula pipe operations.
"""

from abc import ABC, abstractmethod
from typing import Any, List


class BaseCommand(ABC):
    """Base class for all StrataRegula commands."""
    
    name: str = ""
    description: str = ""
    category: str = ""
    input_types: List[str] = []
    output_types: List[str] = []
    
    @abstractmethod
    async def execute(self, data: Any, *args, **kwargs) -> Any:
        """Execute the command with the given data."""
        pass