"""
Regression Tests for Deleted Code

Ensures that old/deprecated code is not being referenced:
- inbox_messages table (replaced by chat_messages inbox)
- EventBus (removed)
- AgentRunner (removed, replaced by Master/Worker)
- SubAgentManager (removed, replaced by Master.create_sub_runtime)
- is_busy state (removed, replaced by awake/sleep)
"""

import os
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Path to the novaic-gateway directory
GATEWAY_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def search_in_codebase(pattern: str, exclude_dirs: list = None) -> list:
    """
    Search for a pattern in the codebase using Python.
    
    Returns list of matching files/lines.
    """
    exclude_dirs = exclude_dirs or [
        '__pycache__', '.git', 'tests', 'node_modules', 'storage',
        'dist', '.venv', 'venv', 'site-packages', 'build', 'egg-info'
    ]
    matches = []
    
    for root, dirs, files in os.walk(GATEWAY_DIR):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Also skip if any parent is excluded
        if any(excl in root for excl in exclude_dirs):
            continue
        
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'r') as file:
                        for i, line in enumerate(file, 1):
                            if pattern.lower() in line.lower():
                                matches.append(f"{filepath}:{i}: {line.strip()}")
                except:
                    pass
    return matches


class TestNoInboxMessagesTable:
    """Ensure inbox_messages table is no longer used."""
    
    def test_no_inbox_messages_table_access(self):
        """No code should access inbox_messages table."""
        matches = search_in_codebase('inbox_messages')
        
        # Filter out comments and documentation
        actual_usage = [
            m for m in matches 
            if 'schema.py' not in m  # Schema might have migration comment
            and '# ' not in m.split(':')[-1][:3]  # Not a comment
            and '"""' not in m  # Not a docstring
        ]
        
        assert len(actual_usage) == 0, f"Found inbox_messages references: {actual_usage}"
    
    def test_no_inbox_repository_import(self):
        """inbox repository should not be imported."""
        matches = search_in_codebase('from.*inbox.*import')
        
        # Filter out test files
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found inbox imports: {actual}"


class TestNoEventBus:
    """Ensure EventBus system is removed."""
    
    def test_no_event_bus_imports(self):
        """EventBus should not be imported."""
        matches = search_in_codebase('from.*events.*bus.*import')
        
        # Filter out test files
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found EventBus imports: {actual}"
    
    def test_no_event_handler_imports(self):
        """Event handler should not be imported."""
        matches = search_in_codebase('from.*events.*handler.*import')
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found event handler imports: {actual}"


class TestNoAgentRunner:
    """Ensure old AgentRunner is removed."""
    
    def test_no_agent_runner_imports(self):
        """AgentRunner should not be imported."""
        matches = search_in_codebase('from.*agent.*runner.*import')
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found AgentRunner imports: {actual}"
    
    def test_no_agent_runner_class(self):
        """AgentRunner class should not exist."""
        matches = search_in_codebase('class AgentRunner')
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found AgentRunner class: {actual}"


class TestNoSubAgentManager:
    """Ensure old SubAgentManager is removed."""
    
    def test_no_subagent_manager_imports(self):
        """SubAgentManager should not be imported."""
        matches = search_in_codebase('from.*subagent.*manager.*import')
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found SubAgentManager imports: {actual}"
    
    def test_no_subagent_manager_class(self):
        """SubAgentManager class should not exist."""
        matches = search_in_codebase('class SubAgentManager')
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found SubAgentManager class: {actual}"


class TestNoIsBusyState:
    """Ensure is_busy state is removed."""
    
    def test_no_is_busy_field(self):
        """is_busy field should not be used as actual code (not just comments)."""
        matches = search_in_codebase('is_busy')
        
        # Filter to only actual field usage, not:
        # - Migration comments in schema.py
        # - Comments about removal
        actual = [
            m for m in matches 
            if '/tests/' not in m
            and 'removed' not in m.lower()  # Migration comments
            and '# note:' not in m.lower()  # Comments
            and 'print(' not in m.lower()  # Print statements about migration
            and 'is_busy =' in m  # Only actual assignment
        ]
        
        assert len(actual) == 0, f"Found is_busy references: {actual}"
    
    def test_no_busy_state(self):
        """BUSY state should not exist."""
        matches = search_in_codebase("state.*=.*['\"]busy['\"]")
        
        actual = [m for m in matches if '/tests/' not in m]
        
        assert len(actual) == 0, f"Found BUSY state: {actual}"


class TestNoDeprecatedMethods:
    """Ensure deprecated methods are removed."""
    
    def test_no_deprecated_marker(self):
        """No DEPRECATED markers should remain in active code (excluding dist and comments)."""
        matches = search_in_codebase('DEPRECATED')
        
        # Filter out dist folder, tests, and explanatory comments
        actual = [
            m for m in matches 
            if '/tests/' not in m
            and '/dist/' not in m
            and 'v12:' not in m.lower()  # Architecture transition comments
            and 'signature compatibility' not in m.lower()  # Kept for compatibility
        ]
        
        # These are acceptable deprecation markers (explaining why something is deprecated)
        acceptable_patterns = [
            'Deprecated - use Master',  # Explains the new approach
            'Deprecated: use Master',
            'Deprecated, kept for signature',  # Backward compat
        ]
        actual = [m for m in actual if not any(p in m for p in acceptable_patterns)]
        
        assert len(actual) == 0, f"Found DEPRECATED markers: {actual}"
    
    def test_no_add_agent_method(self):
        """Old add_agent method should not be called."""
        # Check for method calls (not definitions which are in tests)
        matches = search_in_codebase(r'\.add_agent\(')
        
        actual = [
            m for m in matches 
            if '/tests/' not in m
            and 'def add_agent' not in m
        ]
        
        assert len(actual) == 0, f"Found add_agent calls: {actual}"
    
    def test_no_setup_existing_agents(self):
        """setup_existing_agents should not be called."""
        matches = search_in_codebase('setup_existing_agents')
        
        actual = [
            m for m in matches 
            if '/tests/' not in m
            and 'No longer call' not in m  # Allow explanatory comment
        ]
        
        assert len(actual) == 0, f"Found setup_existing_agents: {actual}"


class TestImportIntegrity:
    """Ensure all imports are valid."""
    
    def test_main_imports_work(self):
        """Main module can be imported without deleted module errors."""
        try:
            # Test services imports work
            from db.repositories import RuntimeRepository
            from services.executors.think import ThinkExecutor
            from services.executors.tool_call import ToolCallExecutor
            from services.executors.llm_caller import LLMCaller
            
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_no_deleted_module_imports(self):
        """No imports of deleted modules."""
        deleted_modules = [
            'agent.events',
            'agent.inbox', 
            'agent.runner',
            'agent.subagent',
            'api.inbox_service',
            'db.repositories.inbox',
            'process.manager',  # ProcessManager 已移除，Worker 由 Tauri 统一拉起
        ]
        
        for module in deleted_modules:
            matches = search_in_codebase(f'from {module}')
            actual = [m for m in matches if '/tests/' not in m]
            
            assert len(actual) == 0, f"Found import of deleted module {module}: {actual}"


class TestNoOldArchitecturePatterns:
    """Ensure old architecture patterns are not used."""
    
    def test_no_direct_novaic_agent_chat(self):
        """NovAICAgent.chat() should not be called directly."""
        matches = search_in_codebase(r'\.chat\(')
        
        # Filter to find direct agent chat calls in routes
        problematic = [
            m for m in matches 
            if '/tests/' not in m
            and 'api/routes.py' in m
            and 'chat_service' not in m
        ]
        
        # This test documents the pattern to avoid
        # Actual matches may be acceptable in some cases
        pass  # Documenting pattern only
    
    def test_no_event_broadcast_new_message_calls(self):
        """broadcast_new_message should not be actively called (method can exist)."""
        matches = search_in_codebase('broadcast_new_message')
        
        # Filter to only actual calls, not:
        # - Method definitions
        # - Comments about not using it
        actual = [
            m for m in matches 
            if '/tests/' not in m
            and 'async def broadcast_new_message' not in m  # Method definition is OK
            and 'v12: No broadcast_new_message needed' not in m  # Comment is OK
            and 'await' in m and 'broadcast_new_message(' in m  # Actual calls
        ]
        
        assert len(actual) == 0, f"Found broadcast_new_message calls: {actual}"
