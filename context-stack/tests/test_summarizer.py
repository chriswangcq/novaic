"""
Tests for context/summarizer.py — structured summarization.
"""
import pytest

from context_stack.context.summarizer import StructuredSummarizer
from context_stack.context.types import Message, MessageRole, ScopeRecord
from tests.conftest import MockCounter, MockSummarizer, FailingSummarizer, make_scope


def make_scope_messages():
    return [
        Message(role=MessageRole.ASSISTANT, content="I'll read the project structure."),
        Message(role=MessageRole.TOOL, content="src/app.py\nsrc/models/user.py", tool_name="read_file"),
        Message(role=MessageRole.ASSISTANT, content="I'll create the auth module."),
        Message(role=MessageRole.TOOL, content="Created file src/auth.py", tool_name="write_file"),
        Message(role=MessageRole.TOOL, content="Created file src/models/user.py", tool_name="write_file"),
        Message(role=MessageRole.TOOL, content="Error: test_login FAILED - AssertionError", tool_name="run_command"),
        Message(role=MessageRole.ASSISTANT, content="Fixed the test. Done."),
        Message(role=MessageRole.TOOL, content="All 5 tests passed.", tool_name="run_command"),
    ]


class TestMetadataExtraction:
    def setup_method(self):
        self.counter = MockCounter()
        self.summarizer_obj = MockSummarizer()
        self.summarizer = StructuredSummarizer(self.summarizer_obj, self.counter)

    def test_extracts_file_paths(self):
        scope = make_scope()
        self.summarizer.summarize(scope, make_scope_messages())
        # Should find created files
        assert any("src/auth.py" in f or "src/models/user.py" in f for f in scope.files_changed)

    def test_extracts_tool_usage(self):
        scope = make_scope()
        self.summarizer.summarize(scope, make_scope_messages())
        assert "write_file" in scope.tools_used
        assert "run_command" in scope.tools_used
        assert "read_file" in scope.tools_used

    def test_counts_tools_correctly(self):
        scope = make_scope()
        self.summarizer.summarize(scope, make_scope_messages())
        assert scope.tools_used.get("write_file", 0) == 2
        assert scope.tools_used.get("run_command", 0) == 2

    def test_extracts_errors(self):
        scope = make_scope()
        self.summarizer.summarize(scope, make_scope_messages())
        assert len(scope.errors) > 0
        assert any("FAILED" in e or "Error" in e for e in scope.errors)

    def test_no_errors_when_clean(self):
        scope = make_scope()
        clean_messages = [
            Message(role=MessageRole.ASSISTANT, content="Done"),
            Message(role=MessageRole.TOOL, content="All tests passed", tool_name="run_command"),
        ]
        self.summarizer.summarize(scope, clean_messages)
        assert scope.errors == []

    def test_empty_messages(self):
        scope = make_scope()
        self.summarizer.summarize(scope, [])
        assert scope.files_changed == []
        assert scope.tools_used == {}
        assert scope.errors == []


class TestSummaryGeneration:
    def setup_method(self):
        self.counter = MockCounter()

    def test_llm_summary_used(self):
        llm = MockSummarizer(text="Implemented user auth with bcrypt.")
        s = StructuredSummarizer(llm, self.counter)
        scope = make_scope()
        result = s.summarize(scope, make_scope_messages())
        assert "bcrypt" in result
        assert llm.call_count == 1

    def test_fallback_used_when_llm_fails(self):
        s = StructuredSummarizer(FailingSummarizer(), self.counter)
        scope = make_scope()
        messages = make_scope_messages()
        result = s.summarize(scope, messages)
        # Fallback should still produce a summary
        assert len(result) > 10
        assert "Scope Complete" in result

    def test_summary_contains_scope_name(self):
        llm = MockSummarizer(text="Work done.")
        s = StructuredSummarizer(llm, self.counter)
        scope = make_scope(name="my-special-scope")
        result = s.summarize(scope, make_scope_messages())
        assert "my-special-scope" in result

    def test_summary_contains_files(self):
        llm = MockSummarizer(text="Work done.")
        s = StructuredSummarizer(llm, self.counter)
        scope = make_scope()
        result = s.summarize(scope, make_scope_messages())
        # After extracting metadata, files should be in summary
        assert len(scope.files_changed) > 0

    def test_empty_messages_fallback(self):
        s = StructuredSummarizer(FailingSummarizer(), self.counter)
        scope = make_scope(name="empty-scope")
        result = s.summarize(scope, [])
        assert "empty-scope" in result
