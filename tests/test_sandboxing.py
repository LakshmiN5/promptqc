import pytest
from promptqc.parser import parse_prompt

def test_single_line_sandboxing():
    text = "<query>{user_input}</query>"
    parsed = parse_prompt(text)
    assert len(parsed.template_variables) == 1
    assert parsed.template_variables[0].is_sandboxed is True

def test_multi_line_sandboxing():
    text = "<context>\nSome data here\n{user_data}\n</context>"
    parsed = parse_prompt(text)
    assert len(parsed.template_variables) == 1
    assert parsed.template_variables[0].is_sandboxed is True

def test_sandboxing_with_surrounding_text():
    text = "Here is the user query: <query>Prompt: {input}</query>"
    parsed = parse_prompt(text)
    assert len(parsed.template_variables) == 1
    assert parsed.template_variables[0].is_sandboxed is True

def test_unsandboxed_variable():
    text = "Summarize this: {user_input}"
    parsed = parse_prompt(text)
    assert len(parsed.template_variables) == 1
    assert parsed.template_variables[0].is_sandboxed is False

def test_multiple_tags_on_line():
    text = "<ignore>ignore this</ignore> <query>{user_input}</query>"
    parsed = parse_prompt(text)
    assert len(parsed.template_variables) == 1
    assert parsed.template_variables[0].is_sandboxed is True

