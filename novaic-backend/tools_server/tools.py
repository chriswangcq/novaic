"""
Tools Server - 工具定义

包含 55 个内置工具的完整定义，符合 OpenAI function calling 格式。

工具分类：
- memory: 10 个工具 (memory_save, memory_recall, memory_delete, memory_list_namespaces, 
                     task_log, task_history, goal_set, goal_progress, goal_complete, session_state)
- runtime: 7 个工具 (runtime_list, runtime_history, runtime_send, runtime_rest,
                     subagent_spawn, subagent_query, subagent_cancel)
- chat: 6 个工具 (chat_reply, chat_ask, chat_notify, chat_show_image, chat_history, chat_get_message)
- web: 2 个工具 (web_search, web_fetch)
- qemu: 5 个工具 (qemu_ssh_exec, qemu_status, qemu_start_vm, qemu_restart_vm, qemu_shutdown_vm)
- task: 5 个工具 (task_async, task_query, task_list, task_cancel, task_summary)
- notebook: 4 个工具 (notebook_write, notebook_list, notebook_read, notebook_update)
- vm: 32 个工具 (完整 VMUSE 工具集)
  - Browser (9): navigate, click, type, screenshot, scroll, evaluate, get_tabs, switch_tab, close_tab
  - Desktop (3): screenshot, mouse, keyboard
  - Shell (2): shell_exec, run_python
  - File (4): read, write, list, info
  - Window (7): list_windows, focus_window, maximize_window, minimize_window, close_window, resize_window, launch_app
  - Context (7): system_snapshot, directory_snapshot, app_state, clipboard_get, clipboard_set, recent_files, environment_info

- drive: 2 个工具 (drive_update_profile, drive_update_relationship)

总计: 73 个工具
"""

from typing import Dict, List, Any, Optional

# ==================== VM Tools Definition (直接定义，不依赖 vmuse_adapter) ====================

VM_TOOLS = [
    {
        "name": "browser_navigate",
        "description": "Navigate browser to a URL in the VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "browser_click",
        "description": "Click element in browser by CSS selector",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector"}
            },
            "required": ["selector"]
        }
    },
    {
        "name": "browser_type",
        "description": "Type text into browser element",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector"},
                "text": {"type": "string", "description": "Text to type"}
            },
            "required": ["selector", "text"]
        }
    },
    {
        "name": "browser_screenshot",
        "description": "Take screenshot of current browser page",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "browser_scroll",
        "description": "Scroll browser page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                "amount": {"type": "integer", "description": "Scroll amount", "default": 500}
            },
            "required": ["direction"]
        }
    },
    {
        "name": "browser_evaluate",
        "description": "Execute JavaScript code in browser",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {"type": "string", "description": "JavaScript code"}
            },
            "required": ["script"]
        }
    },
    {
        "name": "browser_get_tabs",
        "description": "Get list of open browser tabs",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "browser_switch_tab",
        "description": "Switch to browser tab by index (0-based)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "Tab index (0-based)"}
            },
            "required": ["index"]
        }
    },
    {
        "name": "browser_close_tab",
        "description": "Close browser tab by index (current tab if not specified)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "description": "Tab index (0-based), omit to close current tab"}
            },
            "required": []
        }
    },
    {
        "name": "screenshot",
        "description": "Take desktop screenshot of VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "grid": {"type": "boolean", "description": "Show coordinate grid", "default": True}
            },
            "required": []
        }
    },
    {
        "name": "mouse",
        "description": "Control mouse in VM. Use 'aim' to get aim_id, then use aim_id for other actions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["aim", "click", "right_click", "double", "scroll"]},
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "aim_id": {"type": "string"},
                "zoom": {"type": "number", "default": 2.0}
            },
            "required": ["action"]
        }
    },
    {
        "name": "keyboard",
        "description": "Control keyboard in VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["type", "key"]},
                "text": {"type": "string"},
                "keys": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["action"]
        }
    },
    {
        "name": "shell_exec",
        "description": "Execute shell command in VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command"}
            },
            "required": ["command"]
        }
    },
    {
        "name": "run_python",
        "description": "Execute Python code in VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
            },
            "required": ["code"]
        }
    },
    {
        "name": "file_read",
        "description": "Read file from VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_write",
        "description": "Write file to VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "file_list",
        "description": "List directory contents in VM",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "default": "."}
            },
            "required": []
        }
    },
    {
        "name": "file_info",
        "description": "Get file metadata (size, type, permissions, timestamps)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_windows",
        "description": "List all desktop windows with window_id, title, position, size",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "focus_window",
        "description": "Bring window to front by window_id",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Window ID from list_windows"}
            },
            "required": ["window_id"]
        }
    },
    {
        "name": "maximize_window",
        "description": "Maximize window to fill screen",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Window ID from list_windows"}
            },
            "required": ["window_id"]
        }
    },
    {
        "name": "minimize_window",
        "description": "Minimize window to taskbar",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Window ID from list_windows"}
            },
            "required": ["window_id"]
        }
    },
    {
        "name": "close_window",
        "description": "Close window by window_id",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Window ID from list_windows"}
            },
            "required": ["window_id"]
        }
    },
    {
        "name": "resize_window",
        "description": "Resize window to specific dimensions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {"type": "string", "description": "Window ID from list_windows"},
                "width": {"type": "integer", "description": "Width in pixels"},
                "height": {"type": "integer", "description": "Height in pixels"}
            },
            "required": ["window_id", "width", "height"]
        }
    },
    {
        "name": "launch_app",
        "description": "Launch application by name (firefox, chromium, code, terminal, files)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "system_snapshot",
        "description": "Get system state snapshot: windows, clipboard, resources, processes",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "directory_snapshot",
        "description": "Analyze directory structure: tree, project type, statistics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."},
                "max_depth": {"type": "integer", "description": "Maximum depth", "default": 3}
            },
            "required": []
        }
    },
    {
        "name": "app_state",
        "description": "Get application state: windows, processes for specific app",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "clipboard_get",
        "description": "Get clipboard text content",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "clipboard_set",
        "description": "Set clipboard text content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Text to set in clipboard"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "recent_files",
        "description": "Find recently modified files in directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path", "default": "."},
                "hours": {"type": "integer", "description": "Hours to look back", "default": 24},
                "limit": {"type": "integer", "description": "Maximum files to return", "default": 20}
            },
            "required": []
        }
    },
    {
        "name": "environment_info",
        "description": "Get environment information: shell, PATH, installed tools, env vars",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# ==================== Memory Tools (10) ====================

MEMORY_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "memory_save",
        "description": "Save a memory value. Use namespaces to organize related data. Memory is persistent across sessions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Unique key to identify this memory item"
                },
                "value": {
                    "description": "The value to store (can be any JSON-serializable type)"
                },
                "namespace": {
                    "type": "string",
                    "description": "Optional namespace to organize memories (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "memory_recall",
        "description": "Recall memory value(s). Omit key to get all items in namespace. Returns found=true if the key exists.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Optional key to recall. If omitted, returns all items in namespace"
                },
                "namespace": {
                    "type": "string",
                    "description": "Namespace to recall from (default: 'default')",
                    "default": "default"
                }
            },
            "required": []
        }
    },
    {
        "name": "memory_delete",
        "description": "Delete a memory value by key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Key of the memory item to delete"
                },
                "namespace": {
                    "type": "string",
                    "description": "Namespace to delete from (default: 'default')",
                    "default": "default"
                }
            },
            "required": ["key"]
        }
    },
    {
        "name": "memory_list_namespaces",
        "description": "List all memory namespaces. Useful for discovering what data has been stored.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "task_log",
        "description": "Log a task or action for history tracking. Used to record what actions have been performed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Description of the action performed"
                },
                "details": {
                    "type": "string",
                    "description": "Optional additional details about the action"
                },
                "status": {
                    "type": "string",
                    "description": "Status of the action (default: 'completed')",
                    "enum": ["completed", "failed", "in_progress", "pending"],
                    "default": "completed"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "task_history",
        "description": "Get task history. Returns a list of previously logged actions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of history items to return (default: 20)",
                    "default": 20
                },
                "status_filter": {
                    "type": "string",
                    "description": "Optional filter by status",
                    "enum": ["completed", "failed", "in_progress", "pending"]
                }
            },
            "required": []
        }
    },
    {
        "name": "goal_set",
        "description": "Set a goal to track with optional subtasks. Helps organize and track progress on complex tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "The main goal description"
                },
                "subtasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of subtasks to complete"
                }
            },
            "required": ["goal"]
        }
    },
    {
        "name": "goal_progress",
        "description": "Update goal progress by marking subtasks complete or adding progress notes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "completed_subtask": {
                    "type": "string",
                    "description": "Name of subtask to mark as completed (must match exactly)"
                },
                "progress_note": {
                    "type": "string",
                    "description": "Optional note about progress made"
                }
            },
            "required": []
        }
    },
    {
        "name": "goal_complete",
        "description": "Mark current goal as complete with optional summary.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Optional summary of what was accomplished"
                }
            },
            "required": []
        }
    },
    {
        "name": "session_state",
        "description": "Get current session state overview including current goal, recent actions, and memory namespaces.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# ==================== Runtime Tools (7) ====================

RUNTIME_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "runtime_list",
        "description": "List all active runtimes in this agent. Shows main and sub-agent runtimes.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "runtime_history",
        "description": "Get message history for a specific runtime. Useful for reviewing conversation context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_runtime_id": {
                    "type": "string",
                    "description": "Runtime ID to get history for (e.g., 'rt-xxx')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return (default: 50)",
                    "default": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of messages to skip (default: 0)",
                    "default": 0
                }
            },
            "required": ["target_runtime_id"]
        }
    },
    {
        "name": "runtime_send",
        "description": "Send a message to another runtime. Used for inter-runtime communication.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_runtime_id": {
                    "type": "string",
                    "description": "Runtime ID to send message to"
                },
                "message": {
                    "type": "string",
                    "description": "Message content to send"
                }
            },
            "required": ["target_runtime_id", "message"]
        }
    },
    {
        "name": "runtime_rest",
        "description": "Voluntarily enter rest state. The runtime will pause and wait for wake triggers. For Main Runtime: waits for user response. For SubAgent: reports completion to parent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Reason for entering rest state"
                },
                "wake_triggers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["user_response", "timer", "event"]
                            },
                            "config": {"type": "object"}
                        }
                    },
                    "description": "Conditions that will wake the agent (default: user_response)"
                },
                "handoff_notes": {
                    "type": "string",
                    "description": "Optional notes for context when waking up"
                },
                "rest_duration_minutes": {
                    "type": "integer",
                    "description": "How many minutes to rest before auto-waking. Default 30. Range: 1-1440 (24h). The agent will be automatically woken up after this duration.",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 1440
                }
            },
            "required": ["reason"]
        }
    },
    {
        "name": "subagent_spawn",
        "description": "Spawn a SubAgent to execute a task asynchronously. SubAgents run independently and can be queried for status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task description for the SubAgent to execute"
                },
                "share_context": {
                    "type": "boolean",
                    "description": "Whether to share parent context with SubAgent (default: false)",
                    "default": False
                },
                "timeout_minutes": {
                    "type": "integer",
                    "description": "Maximum execution time in minutes (default: 30)",
                    "default": 30
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "subagent_query",
        "description": "Query the status of a spawned SubAgent. Returns current status, progress, and results if completed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_subagent_id": {
                    "type": "string",
                    "description": "SubAgent ID to query (e.g., 'sub-xxx')"
                }
            },
            "required": ["target_subagent_id"]
        }
    },
    {
        "name": "subagent_cancel",
        "description": "Cancel a running SubAgent. Stops execution immediately.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_subagent_id": {
                    "type": "string",
                    "description": "SubAgent ID to cancel"
                }
            },
            "required": ["target_subagent_id"]
        }
    },
]


# ==================== Chat Tools (6) ====================

CHAT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "chat_reply",
        "description": "Send a reply message to the user. The message will be displayed in the chat interface.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message content to send to the user"
                },
                "attachments": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of attachment URLs or file paths"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "chat_ask",
        "description": "Ask the user a question and wait for response. Can provide options for the user to choose from.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question to ask the user"
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of choices for the user"
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "How long to wait for response (default: 300)",
                    "default": 300
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "chat_notify",
        "description": "Send a notification to the user. No response is expected. Good for status updates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Notification message"
                },
                "level": {
                    "type": "string",
                    "description": "Notification level (default: 'info')",
                    "enum": ["info", "warning", "error", "success"],
                    "default": "info"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "chat_show_image",
        "description": "Show an image to the user in the chat interface.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file or URL"
                },
                "caption": {
                    "type": "string",
                    "description": "Optional caption for the image"
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "chat_history",
        "description": "Get recent chat history. Messages are summarized by default.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return (default: 20)",
                    "default": 20
                },
                "summary_length": {
                    "type": "integer",
                    "description": "Maximum length for message summaries (default: 50)",
                    "default": 50
                }
            },
            "required": []
        }
    },
    {
        "name": "chat_get_message",
        "description": "Get full content of a specific chat message by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "ID of the message to retrieve"
                }
            },
            "required": ["message_id"]
        }
    },
]


# ==================== Web Tools (2) ====================

WEB_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "web_search",
        "description": "Search the web using Brave Search API. Returns relevant search results with titles, URLs, and snippets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                    "default": 10
                },
                "freshness": {
                    "type": "string",
                    "description": "Filter results by freshness (e.g., 'day', 'week', 'month')",
                    "enum": ["day", "week", "month"]
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch a web page and convert to markdown. Extracts main content by default.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the web page to fetch"
                },
                "extract_main_content": {
                    "type": "boolean",
                    "description": "Whether to extract only main content (default: true)",
                    "default": True
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum content length (default: 50000)",
                    "default": 50000
                }
            },
            "required": ["url"]
        }
    },
]


# ==================== QEMU Tools (6) ====================

QEMU_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "qemu_ssh_exec",
        "description": "Execute a command via SSH on the QEMU virtual machine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute on the VM"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "qemu_status",
        "description": "Get QEMU VM status including running state, ports, and resource usage.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "qemu_start_vm",
        "description": "Start the QEMU virtual machine. Use this to boot up the VM if it's not running.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "memory": {
                    "type": "string",
                    "description": "Memory size in MB (default: '4096')",
                    "default": "4096"
                },
                "cpus": {
                    "type": "integer",
                    "description": "Number of CPUs (default: 4)",
                    "default": 4
                }
            },
            "required": []
        }
    },
    {
        "name": "qemu_restart_vm",
        "description": "Restart the QEMU virtual machine. This will gracefully shutdown and then start the VM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graceful": {
                    "type": "boolean",
                    "description": "Try graceful shutdown via SSH first (default: true)",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "qemu_shutdown_vm",
        "description": "Shutdown the QEMU virtual machine gracefully. Use this to safely stop the VM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "graceful": {
                    "type": "boolean",
                    "description": "Try graceful shutdown via SSH first (default: true)",
                    "default": True
                },
                "quick": {
                    "type": "boolean",
                    "description": "Use shorter timeouts for faster shutdown (default: false)",
                    "default": False
                }
            },
            "required": []
        }
    },
]


# ==================== Task Tools (5) ====================

TASK_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "task_async",
        "description": "Execute any tool asynchronously in background. Returns a task_id that can be used to query status later.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "Name of the tool to execute"
                },
                "args": {
                    "type": "object",
                    "description": "Arguments to pass to the tool"
                },
                "label": {
                    "type": "string",
                    "description": "Optional human-readable label for this task"
                }
            },
            "required": ["tool"]
        }
    },
    {
        "name": "task_query",
        "description": "Query task status and results. Can retrieve partial output for long-running tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to query"
                },
                "tail_lines": {
                    "type": "integer",
                    "description": "Number of output lines to return from the end"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number for output range"
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number for output range"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_list",
        "description": "List all tasks, optionally filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by task status",
                    "enum": ["pending", "running", "completed", "failed", "cancelled"]
                }
            },
            "required": []
        }
    },
    {
        "name": "task_cancel",
        "description": "Cancel a running task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to cancel"
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for cancellation"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "task_summary",
        "description": "Get AI-generated summary of a completed task. Useful for long outputs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the completed task"
                }
            },
            "required": ["task_id"]
        }
    },
]


# ==================== Notebook Tools (Agent's private workspace) ====================

NOTEBOOK_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "notebook_write",
        "description": "Write a new entry to your private notebook. Use this to record research findings, reflections, insights, plans, or observations. Notebook entries are private and not shown to the user unless you explicitly share them via chat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "enum": ["research", "reflection", "insight", "plan", "observation"],
                    "description": "Type of entry: research (collected info), reflection (thinking about past), insight (discovered know-how), plan (future action items), observation (environmental notes)"
                },
                "title": {
                    "type": "string",
                    "description": "Short title summarizing this entry"
                },
                "content": {
                    "type": "string",
                    "description": "Detailed content of the entry"
                },
                "related_topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Topic tags for categorization (e.g. ['crypto', 'btc', 'market'])"
                },
                "relevance_score": {
                    "type": "number",
                    "description": "How relevant this is to the user (0.0-1.0, default 0.5)",
                    "minimum": 0,
                    "maximum": 1
                },
                "expires_at": {
                    "type": "string",
                    "description": "ISO timestamp when this info expires (for time-sensitive data like prices). Omit for permanent entries."
                }
            },
            "required": ["entry_type", "title", "content"]
        }
    },
    {
        "name": "notebook_list",
        "description": "List entries from your notebook with optional filters. Returns titles and metadata. Use notebook_read to get full content of a specific entry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "enum": ["research", "reflection", "insight", "plan", "observation"],
                    "description": "Filter by entry type"
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "ready", "shared", "archived"],
                    "description": "Filter by status"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max entries to return (default 20)",
                    "default": 20
                },
                "include_expired": {
                    "type": "boolean",
                    "description": "Include expired entries (default false)",
                    "default": False
                }
            },
            "required": []
        }
    },
    {
        "name": "notebook_read",
        "description": "Read the full content of a specific notebook entry by ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_id": {
                    "type": "integer",
                    "description": "ID of the notebook entry to read"
                }
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "notebook_update",
        "description": "Update an existing notebook entry. Use to change status (draft->ready->shared->archived), update content, or adjust relevance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_id": {
                    "type": "integer",
                    "description": "ID of the notebook entry to update"
                },
                "status": {
                    "type": "string",
                    "enum": ["draft", "ready", "shared", "archived"],
                    "description": "New status"
                },
                "content": {
                    "type": "string",
                    "description": "Updated content"
                },
                "title": {
                    "type": "string",
                    "description": "Updated title"
                },
                "relevance_score": {
                    "type": "number",
                    "description": "Updated relevance (0.0-1.0)",
                    "minimum": 0,
                    "maximum": 1
                },
                "expires_at": {
                    "type": "string",
                    "description": "Updated expiry timestamp"
                }
            },
            "required": ["entry_id"]
        }
    },
]


# ==================== Drive Tools (Agent autonomous behavior) ====================

DRIVE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "drive_update_profile",
        "description": "Update your understanding of the user. Store learned preferences, habits, interests, or other observations about the user. This data persists across sessions and helps you be more helpful and relevant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Profile key (e.g. 'interests', 'active_hours', 'tech_stack', 'communication_preference', 'current_project')"
                },
                "value": {
                    "description": "Value to store (string, array, or object)"
                },
                "reason": {
                    "type": "string",
                    "description": "Why you're updating this (for your own reference)"
                }
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "drive_update_relationship",
        "description": "Adjust your relationship metrics with the user based on interaction quality. Use positive deltas when interactions go well, negative when you sense the user is annoyed or unresponsive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "relationship_delta": {
                    "type": "integer",
                    "description": "Change in relationship level (-10 to +10)",
                    "minimum": -10,
                    "maximum": 10
                },
                "proactiveness_delta": {
                    "type": "number",
                    "description": "Change in proactiveness (-0.2 to +0.2)",
                    "minimum": -0.2,
                    "maximum": 0.2
                },
                "reason": {
                    "type": "string",
                    "description": "Why you're adjusting (e.g. 'user responded positively to my suggestion')"
                }
            },
            "required": ["reason"]
        }
    },
]


# ==================== All Tools Combined ====================

BUILTIN_TOOLS: Dict[str, List[Dict[str, Any]]] = {
    "memory": MEMORY_TOOLS,
    "notebook": NOTEBOOK_TOOLS,
    "drive": DRIVE_TOOLS,
    "runtime": RUNTIME_TOOLS,
    "chat": CHAT_TOOLS,
    "web": WEB_TOOLS,
    "qemu": QEMU_TOOLS,
    "task": TASK_TOOLS,
    "vm": VM_TOOLS,  # VM USE tools (browser, desktop, shell, file, window, context)
}

# Tool name to category mapping (for quick lookup)
_TOOL_NAME_TO_CATEGORY: Dict[str, str] = {}
_TOOL_BY_NAME: Dict[str, Dict[str, Any]] = {}

def _build_indexes():
    """Build tool indexes for quick lookup."""
    global _TOOL_NAME_TO_CATEGORY, _TOOL_BY_NAME
    for category, tools in BUILTIN_TOOLS.items():
        for tool in tools:
            name = tool["name"]
            _TOOL_NAME_TO_CATEGORY[name] = category
            _TOOL_BY_NAME[name] = tool

_build_indexes()


# ==================== Helper Functions ====================

def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all tools as a flat list (for LLM function calling).
    
    Includes all builtin tools (including VM tools).
    
    Returns:
        List of tool definitions in OpenAI function calling format.
        Each tool has: name, description, inputSchema
    """
    tools = []
    
    # 添加所有内置工具（包括 VM 工具）
    for category_tools in BUILTIN_TOOLS.values():
        tools.extend(category_tools)
    
    return tools


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a tool definition by name.
    
    Supports both standard builtin tools and VM tools.
    
    Args:
        name: Tool name (e.g., 'memory_save', 'chat_reply', 'browser_navigate')
        
    Returns:
        Tool definition dict or None if not found
    """
    # 首先检查标准内置工具
    tool = _TOOL_BY_NAME.get(name)
    if tool:
        return tool
    
    # 如果不是标准工具，检查是否是 VM 工具
    for vm_tool in VM_TOOLS:
        if vm_tool.get("name") == name:
            return vm_tool
    
    return None


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all tools in a specific category.
    
    Args:
        category: Category name ('memory', 'runtime', 'chat', 'web', 'qemu', 'task')
        
    Returns:
        List of tool definitions in that category
    """
    return BUILTIN_TOOLS.get(category, [])


def get_tool_category(tool_name: str) -> Optional[str]:
    """
    Get the category of a tool by name.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Category name or None if tool not found
    """
    return _TOOL_NAME_TO_CATEGORY.get(tool_name)


def get_tool_count() -> Dict[str, int]:
    """
    Get count of tools per category.
    
    Returns:
        Dict mapping category name to tool count
    """
    return {category: len(tools) for category, tools in BUILTIN_TOOLS.items()}


def format_tools_for_openai() -> List[Dict[str, Any]]:
    """
    Format tools for OpenAI API function calling format.
    
    Returns:
        List of tools in OpenAI format with 'type', 'function' wrapper
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"]
            }
        }
        for tool in get_all_tools()
    ]


# ==================== Tool Statistics ====================

def get_stats() -> Dict[str, Any]:
    """
    Get tool statistics.
    
    Returns:
        Dict with total count, count by category, and tool names
    """
    return {
        "total_tools": len(_TOOL_BY_NAME),
        "by_category": get_tool_count(),
        "categories": list(BUILTIN_TOOLS.keys()),
        "tools": list(_TOOL_BY_NAME.keys()),
    }
