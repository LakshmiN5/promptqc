"""Prompt parser — splits prompts into structured sections and sentences."""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set


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
class TemplateVariable:
    """A template variable found in the prompt."""
    name: str              # Variable name (e.g., "user_input")
    syntax: str            # Full match (e.g., "{user_input}", "{{context}}")
    line: int              # 1-indexed line number
    is_sandboxed: bool     # Whether it's inside XML/delimiter tags
    sandbox_tag: Optional[str] = None  # The tag wrapping it, if any


@dataclass
class ParsedPrompt:
    """Fully parsed prompt with sections and metadata."""
    raw_text: str
    lines: List[PromptLine]
    sections: List[PromptSection]
    template_variables: List[TemplateVariable] = field(default_factory=list)

    @property
    def all_instructions(self) -> List[Tuple[int, str]]:
        """Get all instructions across all sections."""
        result = []
        for section in self.sections:
            result.extend(section.instructions)
        return result

    @property
    def variable_names(self) -> Set[str]:
        """Get all unique template variable names."""
        return {v.name for v in self.template_variables}

    @property
    def unsandboxed_variables(self) -> List[TemplateVariable]:
        """Get template variables that are not wrapped in safe delimiters."""
        return [v for v in self.template_variables if not v.is_sandboxed]

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

# Template variable patterns (order matters: Jinja2 double-braces before single)
_TEMPLATE_PATTERNS = [
    re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}'),   # Jinja2: {{ var }}
    re.compile(r'(?<!\{)\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}(?!\})'),  # Python f-string / .format(): {var}
    re.compile(r'\$\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}'),      # Shell-style: ${var}
]

# Regex for finding XML open and close tags
_XML_OPEN_TAG_INLINE_RE = re.compile(r'<([a-zA-Z_][a-zA-Z0-9_-]*)>')
_XML_CLOSE_TAG_INLINE_RE = re.compile(r'</([a-zA-Z_][a-zA-Z0-9_-]*)>')


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

    # Extract template variables
    template_variables = _extract_template_variables(text)

    return ParsedPrompt(
        raw_text=text,
        lines=parsed_lines,
        sections=sections,
        template_variables=template_variables,
    )


def _build_sandboxed_regions(text: str) -> List[Tuple[int, int, str]]:
    """
    Build a list of XML-tag sandboxed regions across the entire prompt.

    Uses a stack-based state machine to track opening and closing XML tags
    across multiple lines, correctly handling:
    - Multi-line: <context>\n{data}\n</context>
    - Single-line: <query>{input}</query>
    - With surrounding text: <query>User asked: {input}</query>

    Returns:
        List of (start_line, end_line, tag_name) tuples representing
        regions where template variables are considered "sandboxed."
    """
    lines = text.split("\n")
    regions: List[Tuple[int, int, str]] = []

    # Stack of (tag_name, opening_line_number)
    tag_stack: List[Tuple[str, int]] = []

    for i, line in enumerate(lines):
        line_num = i + 1

        # Process all tags on this line in order of their position.
        # We collect both opens and closes, sort by position, and process
        # sequentially to handle multiple tags on one line correctly.
        events: List[Tuple[int, str, str]] = []  # (position, 'open'|'close', tag_name)

        for match in _XML_OPEN_TAG_INLINE_RE.finditer(line):
            events.append((match.start(), "open", match.group(1)))
        for match in _XML_CLOSE_TAG_INLINE_RE.finditer(line):
            events.append((match.start(), "close", match.group(1)))

        # Sort by position so we process left-to-right
        events.sort(key=lambda e: e[0])

        for _, event_type, tag_name in events:
            if event_type == "open":
                tag_stack.append((tag_name, line_num))
            elif event_type == "close":
                # Find matching opening tag (search from top of stack)
                for k in range(len(tag_stack) - 1, -1, -1):
                    if tag_stack[k][0] == tag_name:
                        open_line = tag_stack[k][1]
                        regions.append((open_line, line_num, tag_name))
                        tag_stack.pop(k)
                        break

    return regions


def _extract_template_variables(text: str) -> List[TemplateVariable]:
    """
    Extract template variables from prompt text.

    Detects:
    - Python f-string / .format() style: {variable_name}
    - Jinja2 style: {{ variable_name }}
    - Shell style: ${variable_name}

    Also checks if each variable is "sandboxed" inside XML-like tags
    using a state-machine that tracks tags across multiple lines:
    - <context>\n{user_input}\n</context>  → sandboxed  (multi-line)
    - <query>{user_input}</query>           → sandboxed  (single-line)
    - <query>Prompt: {user_input}</query>   → sandboxed  (with text)
    - Summarize this: {user_input}          → NOT sandboxed (injection risk)
    """
    variables: List[TemplateVariable] = []
    lines = text.split("\n")

    # Step 1: Build sandboxed regions using the state-machine parser
    sandboxed_regions = _build_sandboxed_regions(text)

    # Step 2: Extract all template variables
    seen_on_line: Dict[int, set] = {}  # Avoid duplicate reports on same line
    for i, line in enumerate(lines):
        line_num = i + 1
        seen_on_line[line_num] = set()

        for pattern in _TEMPLATE_PATTERNS:
            for match in pattern.finditer(line):
                var_name = match.group(1)
                full_match = match.group(0)

                # Skip if already seen on this line (Jinja2 pattern might also match single-brace)
                if var_name in seen_on_line[line_num]:
                    continue
                seen_on_line[line_num].add(var_name)

                # Step 3: Check if this variable falls within any sandboxed region
                is_sandboxed = False
                sandbox_tag = None
                for region_start, region_end, region_tag in sandboxed_regions:
                    if region_start <= line_num <= region_end:
                        is_sandboxed = True
                        sandbox_tag = region_tag
                        break

                variables.append(TemplateVariable(
                    name=var_name,
                    syntax=full_match,
                    line=line_num,
                    is_sandboxed=is_sandboxed,
                    sandbox_tag=sandbox_tag,
                ))

    return variables
