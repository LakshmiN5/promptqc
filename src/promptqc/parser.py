"""Prompt parser — splits prompts into structured sections and sentences."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass
class PromptLine:
    """A single line from the prompt with metadata."""
    number: int        # 1-indexed line number
    text: str          # Raw text
    stripped: str       # Stripped text
    is_empty: bool
    is_header: bool
    is_separator: bool
    header_level: int = 0  # 0 = not a header, 1-6 = header level
    section_name: str = ""


@dataclass
class PromptSection:
    """A section of the prompt (e.g., under a ## heading)."""
    name: str
    start_line: int
    end_line: int
    lines: List[PromptLine] = field(default_factory=list)
    level: int = 0  # header level

    @property
    def content(self) -> str:
        return "\n".join(line.text for line in self.lines if not line.is_empty)

    @property
    def instructions(self) -> List[Tuple[int, str]]:
        """Extract individual instructions (bullet points or sentences)."""
        result = []
        for line in self.lines:
            text = line.stripped
            if not text or line.is_header or line.is_separator:
                continue
            # Handle bullet points
            bullet_match = re.match(r'^[-*•]\s+(.+)', text)
            if bullet_match:
                result.append((line.number, bullet_match.group(1).strip()))
            # Handle numbered items
            elif re.match(r'^\d+[.)]\s+', text):
                cleaned = re.sub(r'^\d+[.)]\s+', '', text).strip()
                result.append((line.number, cleaned))
            # Regular text lines
            elif text:
                result.append((line.number, text))
        return result


@dataclass
class ParsedPrompt:
    """Fully parsed prompt with sections and metadata."""
    raw_text: str
    lines: List[PromptLine]
    sections: List[PromptSection]

    @property
    def all_instructions(self) -> List[Tuple[int, str]]:
        """Get all instructions across all sections."""
        result = []
        for section in self.sections:
            result.extend(section.instructions)
        return result

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def non_empty_lines(self) -> int:
        return sum(1 for line in self.lines if not line.is_empty)

    def get_line(self, line_number: int) -> Optional[PromptLine]:
        """Get a line by its 1-indexed number."""
        if 1 <= line_number <= len(self.lines):
            return self.lines[line_number - 1]
        return None

    def get_line_text(self, line_number: int) -> str:
        """Get the text of a line by its 1-indexed number."""
        line = self.get_line(line_number)
        return line.text if line else ""


# Header patterns
_MARKDOWN_HEADER_RE = re.compile(r'^(#{1,6})\s+(.+)')
_SEPARATOR_RE = re.compile(r'^[-=]{3,}\s*$')
_XML_TAG_RE = re.compile(r'^<(\w+)>')
_XML_CLOSE_TAG_RE = re.compile(r'^</(\w+)>')


def parse_prompt(text: str) -> ParsedPrompt:
    """
    Parse a prompt string into structured sections.

    Handles:
    - Markdown headers (# ## ###)
    - XML-style tags (<instructions> </instructions>)
    - Separator lines (--- ===)
    - Bullet points and numbered lists
    """
    raw_lines = text.split("\n")
    parsed_lines: List[PromptLine] = []
    sections: List[PromptSection] = []

    current_section_name = "(preamble)"
    current_section_start = 1
    current_section_level = 0
    current_section_lines: List[PromptLine] = []

    for i, raw_line in enumerate(raw_lines):
        line_num = i + 1
        stripped = raw_line.strip()

        is_empty = len(stripped) == 0
        is_separator = bool(_SEPARATOR_RE.match(stripped))
        is_header = False
        header_level = 0

        # Check markdown headers
        header_match = _MARKDOWN_HEADER_RE.match(stripped)
        if header_match:
            is_header = True
            header_level = len(header_match.group(1))

        # Check XML-style tags
        xml_match = _XML_TAG_RE.match(stripped)
        if xml_match and not _XML_CLOSE_TAG_RE.match(stripped):
            is_header = True
            header_level = 1

        prompt_line = PromptLine(
            number=line_num,
            text=raw_line,
            stripped=stripped,
            is_empty=is_empty,
            is_header=is_header,
            is_separator=is_separator,
            header_level=header_level,
        )
        parsed_lines.append(prompt_line)

        # Start new section on header
        if is_header and not is_empty:
            # Save current section
            if current_section_lines or current_section_name != "(preamble)":
                sections.append(PromptSection(
                    name=current_section_name,
                    start_line=current_section_start,
                    end_line=line_num - 1,
                    lines=current_section_lines,
                    level=current_section_level,
                ))

            # Determine new section name
            if header_match:
                current_section_name = header_match.group(2).strip()
            elif xml_match:
                current_section_name = xml_match.group(1).strip()
            else:
                current_section_name = stripped

            current_section_start = line_num
            current_section_level = header_level
            current_section_lines = [prompt_line]
            prompt_line.section_name = current_section_name
        else:
            current_section_lines.append(prompt_line)
            prompt_line.section_name = current_section_name

    # Save final section
    if current_section_lines:
        sections.append(PromptSection(
            name=current_section_name,
            start_line=current_section_start,
            end_line=len(parsed_lines),
            lines=current_section_lines,
            level=current_section_level,
        ))

    return ParsedPrompt(
        raw_text=text,
        lines=parsed_lines,
        sections=sections,
    )
