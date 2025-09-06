"""
Unified CLI Output Utilities for StrataRegula

Provides consistent output handling across all CLI commands with proper
stdout/stderr separation and cross-platform compatibility.
"""

import sys
from typing import Any, Optional
import json


def sanitize_for_output(content: str, encoding: str = "utf-8") -> str:
    """
    Sanitize content for safe CLI output across platforms.

    Args:
        content: The content to sanitize
        encoding: Target encoding (default: utf-8)

    Returns:
        Sanitized content safe for CLI output
    """
    if not content:
        return ""

    try:
        # Ensure content is properly encoded
        if isinstance(content, bytes):
            content = content.decode(encoding, errors='replace')

        # Remove or replace problematic characters for Windows console
        # Replace common problematic Unicode characters
        replacements = {
            '\u2713': '✓',  # Check mark
            '\u2717': '✗',  # Cross mark
            '\u2022': '•',  # Bullet point
            '\u2753': '?',  # Question mark ornament
            '\ud83d\udd0d': '[SEARCH]',  # Magnifying glass
            '\ud83d\udee0\ufe0f': '[TOOLS]',  # Hammer and wrench
        }

        for problematic, replacement in replacements.items():
            content = content.replace(problematic, replacement)

        # Ensure final output is encodable in target encoding
        content.encode(encoding)
        return content

    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback: ASCII-safe version
        return content.encode('ascii', errors='replace').decode('ascii')


def output_content(content: str, file_path: Optional[str] = None) -> None:
    """
    Output actual content to stdout or file.

    Args:
        content: Content to output
        file_path: Optional file path to write to instead of stdout
    """
    sanitized_content = sanitize_for_output(content)

    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
        except Exception as e:
            # Fallback to stderr for error reporting
            status_message(f"Error writing to {file_path}: {e}", level="error")
    else:
        # Output to stdout
        print(sanitized_content, end='')


def status_message(message: str, level: str = "info") -> None:
    """
    Output status/info messages to stderr.

    Args:
        message: Status message to output
        level: Message level (info, warning, error, success)
    """
    sanitized_message = sanitize_for_output(message)

    # Add level prefixes for clarity
    prefixes = {
        "info": "",
        "success": "✓ ",
        "warning": "⚠ ",
        "error": "✗ ",
    }

    prefix = prefixes.get(level, "")
    formatted_message = f"{prefix}{sanitized_message}"

    # Always output status messages to stderr
    print(formatted_message, file=sys.stderr)


def output_json(data: Any, file_path: Optional[str] = None, indent: int = 2) -> None:
    """
    Output JSON data with consistent formatting.

    Args:
        data: Data to serialize as JSON
        file_path: Optional file path to write to instead of stdout
        indent: JSON indentation level
    """
    try:
        json_content = json.dumps(
            data,
            indent=indent,
            ensure_ascii=False,
            default=str
        )
        output_content(json_content, file_path)
    except Exception as e:
        status_message(f"Error serializing JSON: {e}", level="error")


def progress_message(message: str, current: int, total: int) -> None:
    """
    Output progress messages to stderr.

    Args:
        message: Progress message
        current: Current progress count
        total: Total count
    """
    if total > 0:
        percentage = (current / total) * 100
        formatted_message = f"{message}: {current}/{total} ({percentage:.1f}%)"
    else:
        formatted_message = f"{message}: {current}/{total}"

    status_message(formatted_message)


def compilation_banner(action: str) -> None:
    """
    Output compilation banner messages.

    Args:
        action: Action being performed (e.g., "Starting compilation")
    """
    status_message(f"=== {action} ===")
