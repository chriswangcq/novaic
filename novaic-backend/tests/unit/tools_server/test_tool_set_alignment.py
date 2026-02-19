from common.tools.definitions import BUILTIN_TOOLS
from tools_server.executor import (
    BUILTIN_TOOL_NAMES,
    DEFINED_BUILTIN_TOOL_NAMES,
    INTERNAL_ONLY_BUILTIN_TOOL_NAMES,
)


def _collect_definition_tool_names() -> set[str]:
    names: set[str] = set()
    for tools in BUILTIN_TOOLS.values():
        for tool in tools:
            name = tool.get("name")
            if name:
                names.add(name)
    return names


def test_defined_tool_names_match_definitions():
    assert DEFINED_BUILTIN_TOOL_NAMES == _collect_definition_tool_names()


def test_builtin_tool_names_are_definition_plus_internal_only():
    assert BUILTIN_TOOL_NAMES == (
        DEFINED_BUILTIN_TOOL_NAMES | INTERNAL_ONLY_BUILTIN_TOOL_NAMES
    )


def test_internal_only_tools_do_not_overlap_definitions():
    assert DEFINED_BUILTIN_TOOL_NAMES.isdisjoint(INTERNAL_ONLY_BUILTIN_TOOL_NAMES)
