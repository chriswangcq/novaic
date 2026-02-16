"""
Tools Server - 工具定义（精简版）

优化后的工具集，去除冗余和低频工具。

工具分类：
- runtime: 8 个工具（Agent/SubAgent 管理）
- chat: 3 个工具（用户交互）
- memory: 4 个工具（键值存储）
- task: 7 个工具（任务管理）
- notebook: 4 个工具（笔记记录）
- qemu: 2 个工具（VM 状态管理）
- vm: 25 个工具（Desktop 自动化）
  - Browser (9): navigate, click, type, screenshot, scroll, evaluate, get_tabs, switch_tab, close_tab
  - Desktop (3): screenshot, mouse, keyboard
  - Shell (1): shell_exec
  - File (4): read, write, list, info
  - Window (3): list_windows, focus_window, launch_app
  - Context (4): system_snapshot, directory_snapshot, clipboard_get, clipboard_set
- mobile: 12 个工具（Android 设备控制）
  - Core (4): screenshot, touch, input, shell
  - App (3): install, launch, list
  - UI (2): dump, find
  - File (3): push, pull, list

总计: 65 个工具（从 102 精简）
"""

from typing import Dict, List, Any, Optional

# ==================== VM Tools ====================

VM_TOOLS = [
    {
        "name": "browser_navigate",
        "description": "Navigate browser to a URL in the VM. Waits for page load. Returns success status and any navigation errors. Use to open web pages for automation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to navigate to"
                }
            },
            "required": [
                "url"
            ]
        }
    },
    {
        "name": "browser_click",
        "description": "Click an element in the browser by CSS selector. Waits for element to be clickable. Returns success status. Use for interacting with buttons, links, and clickable elements.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector"
                }
            },
            "required": [
                "selector"
            ]
        }
    },
    {
        "name": "browser_type",
        "description": "Type text into a browser element specified by CSS selector. Clears existing content first. Returns success status. Use for filling forms and search boxes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type"
                }
            },
            "required": [
                "selector",
                "text"
            ]
        }
    },
    {
        "name": "browser_screenshot",
        "description": "Take a screenshot of the current browser page. Returns file_url in File Service. Use display(file_url) to show to LLM for analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "browser_scroll",
        "description": "Scroll the browser page in a direction (up/down/left/right) by specified amount (default 500px). Use to reveal content not visible in viewport or navigate long pages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": [
                        "up",
                        "down",
                        "left",
                        "right"
                    ]
                },
                "amount": {
                    "type": "integer",
                    "description": "Scroll amount",
                    "default": 500
                }
            },
            "required": [
                "direction"
            ]
        }
    },
    {
        "name": "browser_evaluate",
        "description": "Execute JavaScript code in the browser context. Returns the script result or error. Use for extracting data, manipulating DOM, or checking page state that CSS selectors can't reach.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "JavaScript code"
                }
            },
            "required": [
                "script"
            ]
        }
    },
    {
        "name": "browser_get_tabs",
        "description": "Get list of all open browser tabs with their URLs and titles. Returns array of tab info. Use to manage multiple tabs or check what's currently open.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "browser_switch_tab",
        "description": "Switch to a browser tab by its index (0-based). Returns success status. Use to work with multiple tabs in parallel or switch context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "Tab index (0-based)"
                }
            },
            "required": [
                "index"
            ]
        }
    },
    {
        "name": "browser_close_tab",
        "description": "Close a browser tab by index (current tab if not specified). Returns success status. Use to clean up after scraping or close unwanted tabs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "Tab index (0-based), omit to close current tab"
                }
            },
            "required": []
        }
    },
    {
        "name": "screenshot",
        "description": "Take a desktop screenshot of the VM with optional coordinate grid overlay. Grid displays pixel coordinates for precise positioning. Returns file_url in File Service. Use display(file_url) to show to LLM for analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "grid": {
                    "type": "boolean",
                    "description": "Show coordinate grid",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "mouse",
        "description": "Control mouse in VM with two-phase aim workflow. Phase 1: call action='aim' with x,y to get a zoomed crosshair screenshot and an aim_id. You can refine aim with delta-based re-aim, then execute click/right_click/double/scroll using aim_id. aim_id is reusable within TTL (10 minutes).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "aim",
                        "click",
                        "right_click",
                        "double",
                        "scroll"
                    ]
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate for action=aim"
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate for action=aim"
                },
                "aim_id": {
                    "type": "string",
                    "description": "Aim ID from a previous aim step. Required for click/right_click/double/scroll, and for delta-based re-aim."
                },
                "zoom": {
                    "type": "number",
                    "description": "Zoom factor for action=aim (typical range: 2-10)",
                    "default": 2.0
                }
            },
            "required": [
                "action"
            ]
        }
    },
    {
        "name": "keyboard",
        "description": "Control keyboard in VM. 'type' action inputs text character by character. 'key' action sends special keys or combinations (Ctrl+C, Enter, etc.). Supports modifiers: ctrl, alt, shift, meta. Use for text input or keyboard shortcuts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "type",
                        "key"
                    ]
                },
                "text": {
                    "type": "string"
                },
                "keys": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "action"
            ]
        }
    },
    {
        "name": "shell_exec",
        "description": "Execute a shell command in the VM. Returns stdout, stderr, exit_code, and execution duration. Command runs in bash. Supports timeouts. Use for system operations, file manipulation, or running scripts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command"
                }
            },
            "required": [
                "command"
            ]
        }
    },
    {
        "name": "display",
        "description": "Display a file from File Service for LLM context. Use when you need to show an image, audio, video, or text file to the LLM. Returns the file in LLM-ready format. Call this with file_url from previous tool results (screenshot, file_pull, etc.) when you want the LLM to analyze that file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File Service URL (e.g. /api/files/images/agent-xxx/screenshot.png)"
                },
                "modality": {
                    "type": "string",
                    "description": "Optional: image | audio | video | text. Auto-detected from file if omitted.",
                    "enum": ["image", "audio", "video", "text"]
                }
            },
            "required": ["file_url"]
        }
    },
    {
        "name": "file_pull",
        "description": "Pull a file from VM to File Service. Specify path on VM. File is stored and file_url is returned for use with file_push. Use to download files from VM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path on VM (e.g. /tmp/config.json)"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_push",
        "description": "Push a file from File Service to VM. Specify file_url (from file_pull or other tool) and target path on VM. Use to upload files to VM.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File Service URL (e.g. /api/files/binaries/agent-xxx/file.txt)"
                },
                "path": {
                    "type": "string",
                    "description": "Target path on VM"
                }
            },
            "required": ["file_url", "path"]
        }
    },
    {
        "name": "list_windows",
        "description": "List all open windows in the VM with their IDs, titles, positions (x, y), sizes (width, height), and focus state. Use to identify window IDs for focus operations or monitor running applications.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "focus_window",
        "description": "Bring a window to front and give it keyboard focus by window_id or title. Returns success status. Use to switch between applications before performing keyboard/mouse operations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "window_id": {
                    "type": "string",
                    "description": "Window ID from list_windows"
                }
            },
            "required": [
                "window_id"
            ]
        }
    },
    {
        "name": "launch_app",
        "description": "Launch an application in the VM by name (e.g., 'firefox', 'code', 'terminal'). Optionally pass arguments. Returns success status and PID. Use to open applications before automating them.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Application name"
                }
            },
            "required": [
                "app_name"
            ]
        }
    },
    {
        "name": "system_snapshot",
        "description": "Capture a comprehensive snapshot of VM system state: open windows, clipboard content, CPU/memory usage, running processes, and disk space. Returns structured JSON. Use for environment analysis or debugging.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "directory_snapshot",
        "description": "Analyze directory structure and contents with optional depth limit. Returns tree structure with file counts, total sizes, and project type detection. Use to understand project layout or find specific files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path",
                    "default": "."
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth",
                    "default": 3
                }
            },
            "required": []
        }
    },
    {
        "name": "clipboard_get",
        "description": "Get current clipboard content from the VM. Returns text, image data (base64), or file paths depending on clipboard type. Use to retrieve copied data or integrate with copy-paste workflows.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "clipboard_set",
        "description": "Set clipboard content in the VM. Supports text and image data (base64). Use to prepare data for paste operations or share data between automation steps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Text to set in clipboard"
                }
            },
            "required": [
                "content"
            ]
        }
    },
]


# ==================== Memory Tools ====================

MEMORY_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "memory_save",
        "description": "Save a key-value pair to persistent memory with optional namespace. Memory data is automatically loaded in system prompt, so you can reference it directly without recall. Use this to update user preferences, settings, or learned facts. Data survives agent restarts and is shared across all runtimes.",
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
            "required": [
                "key",
                "value"
            ]
        }
    },
    {
        "name": "memory_delete",
        "description": "Delete a key-value pair from memory. Use to clean up temporary data or remove outdated information. The deletion takes effect immediately and will be reflected in future system prompts. Returns success status.",
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
            "required": [
                "key"
            ]
        }
    }
]

# Task History Tools (separate from memory)
TASK_HISTORY_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "task_log",
        "description": "Log an action or task execution to history. Records action description, details, and status (completed/failed/in_progress). Creates a timestamped entry for tracking what has been done.",
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
                    "enum": [
                        "completed",
                        "failed",
                        "in_progress",
                        "pending"
                    ],
                    "default": "completed"
                }
            },
            "required": [
                "action"
            ]
        }
    },
    {
        "name": "task_history",
        "description": "Get task execution history. Returns list of logged actions with timestamps and statuses. Supports filtering by status and limiting results. Use to review past activities.",
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
                    "enum": [
                        "completed",
                        "failed",
                        "in_progress",
                        "pending"
                    ]
                }
            },
            "required": []
        }
    },
]


# ==================== Runtime Tools ====================

RUNTIME_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "runtime_list",
        "description": "List all active runtimes (main agent and subagents). Returns runtime IDs, types, statuses, and creation times. Use this to monitor running tasks and get runtime IDs for communication.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "runtime_history",
        "description": "Get message history of a specific runtime to understand its conversation context. Useful for reviewing SubAgent execution process or debugging message flow. Supports pagination with limit and offset.",
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
            "required": [
                "target_runtime_id"
            ]
        }
    },
    {
        "name": "runtime_send",
        "description": "Send a message to another runtime (Agent or SubAgent). Enables inter-agent communication and coordination. Messages are queued asynchronously. Can wake up resting runtimes.",
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
            "required": [
                "target_runtime_id",
                "message"
            ]
        }
    },
    {
        "name": "runtime_rest",
        "description": "Put runtime into resting state with wake-up conditions. Main runtime waits for user reply or timer. SubAgent can set need_rest=1 to signal completion and wait for parent to acknowledge.",
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
                                "enum": [
                                    "user_response",
                                    "timer",
                                    "event"
                                ]
                            },
                            "config": {
                                "type": "object"
                            }
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
            "required": [
                "reason"
            ]
        }
    },
    {
        "name": "subagent_spawn",
        "description": "Create a new SubAgent to execute tasks in parallel. Specify task description, model, and tools. SubAgent runs independently with its own runtime and can report results back to parent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task description for the SubAgent to execute"
                },
                "share_context": {
                    "type": "boolean",
                    "description": "Whether to share parent context with SubAgent (default: False)",
                    "default": False
                },
                "timeout_minutes": {
                    "type": "integer",
                    "description": "Maximum execution time in minutes (default: 30)",
                    "default": 30
                }
            },
            "required": [
                "task"
            ]
        }
    },
    {
        "name": "subagent_query",
        "description": "Query SubAgent status and results. Returns execution state (running/completed/failed/cancelled), progress, and final results if completed. Use for monitoring parallel tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_subagent_id": {
                    "type": "string",
                    "description": "SubAgent ID to query (e.g., 'sub-xxx')"
                }
            },
            "required": [
                "target_subagent_id"
            ]
        }
    },
    {
        "name": "subagent_cancel",
        "description": "Cancel a running SubAgent by its subagent_id. The SubAgent's runtime will be marked as cancelled. Use when task is no longer needed or taking too long.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_subagent_id": {
                    "type": "string",
                    "description": "SubAgent ID to cancel"
                }
            },
            "required": [
                "target_subagent_id"
            ]
        }
    },
    {
        "name": "subagent_report",
        "description": "Report results from SubAgent to parent Agent. Includes status (completed/failed) and result data. This is how SubAgents communicate their final output back to the parent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "The execution result or findings to report to parent agent. Should include key findings, conclusions, and any issues encountered."
                }
            },
            "required": [
                "result"
            ]
        }
    },
]


# ==================== Chat Tools ====================

CHAT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "chat_reply",
        "description": "Send a reply message to the user. Non-blocking, supports attachments (images, files via File Service URLs). Message is broadcasted via SSE to frontend in real-time. Use for status updates, results, notifications, and sharing files/images with user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message content to send to the user"
                },
                "attachments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "File Service URL (e.g. /api/files/images/agent-xxx/screenshot.png)"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Display filename"
                            },
                            "mime_type": {
                                "type": "string",
                                "description": "MIME type (e.g. image/png)"
                            }
                        },
                        "required": ["url"]
                    },
                    "description": "Optional list of file attachments to show in chat (images will be displayed inline)"
                }
            },
            "required": [
                "message"
            ]
        }
    },
    {
        "name": "chat_history",
        "description": "Get recent chat history with optional summarization. Returns messages with roles (user/assistant/tool) and timestamps. Use to understand context and avoid redundant questions.",
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
]


# ==================== Web Tools (已删除) ====================

WEB_TOOLS: List[Dict[str, Any]] = []


# ==================== QEMU Tools ====================

QEMU_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "qemu_ssh_exec",
        "description": "Execute a command on the QEMU virtual machine via SSH. Returns stdout, stderr, and exit code. Supports custom timeout. Use for remote command execution, deployment, or checking VM state.",
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
            "required": [
                "command"
            ]
        }
    },
    {
        "name": "qemu_status",
        "description": "Get the status and resource usage of the QEMU VM. Returns CPU usage, memory usage, disk usage, network stats, and uptime. Use for monitoring VM health and resource consumption.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]


# ==================== Notebook Tools ====================

NOTEBOOK_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "notebook_write",
        "description": "Create a new entry in your private notebook. Specify entry_type (research/reflection/insight/plan/observation), title, content, related topics, and relevance score. Use for recording findings, ideas, or important information that should be preserved long-term.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "enum": [
                        "research",
                        "reflection",
                        "insight",
                        "plan",
                        "observation"
                    ],
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
                    "items": {
                        "type": "string"
                    },
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
            "required": [
                "entry_type",
                "title",
                "content"
            ]
        }
    },
    {
        "name": "notebook_list",
        "description": "List notebook entries with filters by entry_type, status (draft/ready/shared/archived), and limit. Returns titles and metadata without full content. Use to browse your knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "enum": [
                        "research",
                        "reflection",
                        "insight",
                        "plan",
                        "observation"
                    ],
                    "description": "Filter by entry type"
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "draft",
                        "ready",
                        "shared",
                        "archived"
                    ],
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
        "description": "Read the full content of a specific notebook entry by entry_id. Returns complete entry including title, content, type, topics, score, and timestamps. Use when you need to review detailed notes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_id": {
                    "type": "integer",
                    "description": "ID of the notebook entry to read"
                }
            },
            "required": [
                "entry_id"
            ]
        }
    },
    {
        "name": "notebook_update",
        "description": "Update an existing notebook entry. Can change status (draft→ready→shared→archived), content, title, relevance_score, or expiry date. Use to refine notes or mark them for different lifecycle stages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_id": {
                    "type": "integer",
                    "description": "ID of the notebook entry to update"
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "draft",
                        "ready",
                        "shared",
                        "archived"
                    ],
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
            "required": [
                "entry_id"
            ]
        }
    },
]


# ==================== Quadrant Task Tools ====================

QUADRANT_TASK_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "task_create",
        "description": "Create a new task in the four-quadrant system (q1-q4 based on urgency/importance). Specify title, quadrant, task_type (learning/user_need/system), description, and optional due date. Use to capture TODOs from conversation or proactively identify user needs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "任务标题（简洁描述）"
                },
                "quadrant": {
                    "type": "string",
                    "enum": [
                        "q1",
                        "q2",
                        "q3",
                        "q4"
                    ],
                    "description": "四象限分类"
                },
                "source": {
                    "type": "string",
                    "enum": [
                        "user_request",
                        "user_mention",
                        "inference",
                        "curiosity",
                        "learning",
                        "self_improvement"
                    ],
                    "description": "任务来源"
                },
                "task_type": {
                    "type": "string",
                    "enum": [
                        "one_time",
                        "recurring",
                        "ongoing"
                    ],
                    "description": "任务类型：one_time(一次性), recurring(周期性), ongoing(持续性)，默认 one_time"
                },
                "description": {
                    "type": "string",
                    "description": "任务详细描述（可选）"
                },
                "reasoning": {
                    "type": "string",
                    "description": "为什么创建这个任务（你的推理过程）"
                },
                "due_date": {
                    "type": "string",
                    "description": "截止日期，如 2024-01-20（可选）"
                },
                "context": {
                    "type": "string",
                    "description": "相关上下文，如用户原话（可选）"
                }
            },
            "required": [
                "title",
                "quadrant",
                "source"
            ]
        }
    },
    {
        "name": "task_complete",
        "description": "Mark a task as completed and optionally add completion notes. Updates task status to 'done' and records completion timestamp. Use when task execution is finished.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "任务 ID"
                },
                "notes": {
                    "type": "string",
                    "description": "完成备注/反思（可选）"
                }
            },
            "required": [
                "task_id"
            ]
        }
    },
    {
        "name": "task_update",
        "description": "Update task properties: status (pending/in_progress/done/cancelled), quadrant, title, or due_date. Use to reflect progress or priority changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "任务 ID"
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "pending",
                        "in_progress",
                        "completed",
                        "ongoing",
                        "paused",
                        "cancelled"
                    ],
                    "description": "新状态：pending(待处理), in_progress(进行中), completed(已完成), ongoing(持续进行), paused(暂停), cancelled(取消)"
                },
                "quadrant": {
                    "type": "string",
                    "enum": [
                        "q1",
                        "q2",
                        "q3",
                        "q4"
                    ],
                    "description": "更新象限（优先级变化时）"
                },
                "title": {
                    "type": "string",
                    "description": "更新标题"
                },
                "due_date": {
                    "type": "string",
                    "description": "更新截止日期"
                }
            },
            "required": [
                "task_id"
            ]
        }
    },
    {
        "name": "task_board_list",
        "description": "List tasks from the task board with optional filters by quadrant (q1/q2/q3/q4) and status. Returns task details including title, description, due dates, and metadata. Use to view current TODO items.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "quadrant": {
                    "type": "string",
                    "enum": [
                        "q1",
                        "q2",
                        "q3",
                        "q4",
                        "all"
                    ],
                    "description": "筛选象限，默认 all"
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "pending",
                        "in_progress",
                        "completed",
                        "all"
                    ],
                    "description": "筛选状态，默认 pending"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回数量限制，默认 20"
                }
            }
        }
    },
    {
        "name": "task_delete",
        "description": "Permanently delete a task by task_id. Use to remove completed tasks or cancelled items that are no longer relevant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "任务 ID"
                }
            },
            "required": [
                "task_id"
            ]
        }
    },
]


# ==================== Mobile Tools ====================

MOBILE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "mobile_screenshot",
        "description": "Capture Android device screen. Returns file_url in File Service. Use display(file_url) to show to LLM for analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "grid": {
                    "type": "boolean",
                    "description": "Show coordinate grid overlay",
                    "default": True
                },
                "region": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "integer"
                        },
                        "y": {
                            "type": "integer"
                        },
                        "width": {
                            "type": "integer"
                        },
                        "height": {
                            "type": "integer"
                        }
                    },
                    "description": "Optional region to capture"
                }
            },
            "required": []
        }
    },
    {
        "name": "mobile_touch",
        "description": "Perform Android touch control with strict two-phase aim workflow. Phase 1: action='aim' with x,y returns aim_id and a zoomed screenshot. Phase 2: all coordinate actions must use aim_id (no direct execute coordinates). For swipe, provide both start aim_id and end_aim_id. aim_id is reusable within TTL (10 minutes).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "aim",
                        "tap",
                        "double_tap",
                        "long_press",
                        "swipe",
                        "scroll"
                    ]
                },
                "x": {
                    "type": "integer",
                    "description": "X coordinate for action=aim"
                },
                "y": {
                    "type": "integer",
                    "description": "Y coordinate for action=aim"
                },
                "aim_id": {
                    "type": "string",
                    "description": "Start Aim ID from previous aim action. Required for tap/double_tap/long_press/swipe/scroll."
                },
                "zoom": {
                    "type": "number",
                    "description": "Zoom factor for aim (default 2.0)",
                    "default": 2.0
                },
                "duration": {
                    "type": "integer",
                    "description": "Duration in ms (used by long_press/swipe/scroll)"
                },
                "end_aim_id": {
                    "type": "string",
                    "description": "End Aim ID for swipe destination (required for action=swipe)"
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "left", "right"],
                    "description": "Scroll direction (required for action=scroll)"
                },
                "distance": {
                    "type": "integer",
                    "description": "Scroll distance in pixels (used by action=scroll; default 500)"
                }
            },
            "required": [
                "action"
            ]
        }
    },
    {
        "name": "mobile_input",
        "description": "Input text or send key events to Android device. Supports typing text and special keys (KEYCODE_ENTER, KEYCODE_BACK, etc.). Use for form filling or keyboard shortcuts in mobile apps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "text",
                        "key"
                    ]
                },
                "text": {
                    "type": "string",
                    "description": "Text to input (for action=text)"
                },
                "keycode": {
                    "type": "integer",
                    "description": "Android keycode (for action=key). Common: BACK=4, HOME=3, ENTER=66"
                }
            },
            "required": [
                "action"
            ]
        }
    },
    {
        "name": "mobile_shell",
        "description": "Execute ADB shell command on Android device. Returns stdout, stderr, and exit code. Use for system operations, file manipulation, or checking device state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds",
                    "default": 30
                }
            },
            "required": [
                "command"
            ]
        }
    },
    {
        "name": "mobile_app_install",
        "description": "Install an APK on Android device. The APK must come from File Service (file_url from mobile_file_pull or other tool). Returns success status and package name. Use for app deployment or testing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File Service URL of the APK (e.g. /api/files/apk/agent-xxx/app.apk from mobile_file_pull)"
                },
                "allow_downgrade": {
                    "type": "boolean",
                    "description": "Allow downgrade installation",
                    "default": False
                }
            },
            "required": [
                "file_url"
            ]
        }
    },
    {
        "name": "mobile_app_launch",
        "description": "Launch an installed Android app by package name or intent. Returns success status. Use to open apps before automation or testing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Package name to launch"
                },
                "activity": {
                    "type": "string",
                    "description": "Optional activity name"
                }
            },
            "required": [
                "package_name"
            ]
        }
    },
    {
        "name": "mobile_app_list",
        "description": "List all installed apps on Android device with package names, labels, version codes, and system/user flags. Use to check installed apps or find package names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "third_party_only": {
                    "type": "boolean",
                    "description": "Only list third-party apps",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "mobile_ui_dump",
        "description": "Dump the current UI hierarchy as XML. Returns UI tree with all elements, their properties (bounds, class, text, resource-id), and structure. Use for UI analysis or element identification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "compressed": {
                    "type": "boolean",
                    "description": "Return compressed output with key attributes only",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "mobile_ui_find",
        "description": "Find UI elements by criteria: text, resource-id, class, content-desc, or xpath. Returns matching elements with bounds and properties. Use to locate elements for interaction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Find by exact text"
                },
                "text_contains": {
                    "type": "string",
                    "description": "Find by text containing"
                },
                "resource_id": {
                    "type": "string",
                    "description": "Find by resource ID"
                },
                "class": {
                    "type": "string",
                    "description": "Find by class name"
                },
                "content_desc": {
                    "type": "string",
                    "description": "Find by content description"
                },
                "clickable_only": {
                    "type": "boolean",
                    "description": "Only return clickable elements",
                    "default": False
                }
            },
            "required": []
        }
    },
    {
        "name": "mobile_file_push",
        "description": "Push a file to Android device. The file must come from File Service (file_url from a previous mobile_file_pull or other tool). Returns success status. Use for deploying test data or configuration files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_url": {
                    "type": "string",
                    "description": "File Service URL (e.g. /api/files/images/agent-xxx/filename.png from previous mobile_file_pull result)"
                },
                "remote_path": {
                    "type": "string",
                    "description": "Target path on device (e.g. /sdcard/Download/file.png)"
                }
            },
            "required": [
                "file_url",
                "remote_path"
            ]
        }
    },
    {
        "name": "mobile_file_pull",
        "description": "Pull a file from Android device. File is stored in File Service and a result_id is returned for LLM context. Use file_url from the result when pushing back with mobile_file_push.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "remote_path": {
                    "type": "string",
                    "description": "File path on device (e.g. /sdcard/Download/photo.png)"
                }
            },
            "required": [
                "remote_path"
            ]
        }
    },
    {
        "name": "mobile_file_list",
        "description": "List files and directories on Android device at specified path. Returns array with names, types (file/directory), sizes, and permissions. Use to browse device filesystem.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path on device"
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Show hidden files",
                    "default": False
                }
            },
            "required": [
                "path"
            ]
        }
    },
]


# ==================== Drive Tools (已删除) ====================

DRIVE_TOOLS: List[Dict[str, Any]] = []


# ==================== All Tools Combined ====================

BUILTIN_TOOLS: Dict[str, List[Dict[str, Any]]] = {
    "memory": MEMORY_TOOLS,
    "task_history": TASK_HISTORY_TOOLS,
    "notebook": NOTEBOOK_TOOLS,
    "drive": DRIVE_TOOLS,
    "quadrant_task": QUADRANT_TASK_TOOLS,
    "runtime": RUNTIME_TOOLS,
    "chat": CHAT_TOOLS,
    "web": WEB_TOOLS,
    "qemu": QEMU_TOOLS,
    "vm": VM_TOOLS,
    "mobile": MOBILE_TOOLS,
}

# Tool name to category mapping (for quick lookup)
_TOOL_NAME_TO_CATEGORY: Dict[str, str] = {}
_TOOL_BY_NAME: Dict[str, Dict[str, Any]] = {}

def _build_indexes():
    """Build tool indexes for quick lookup."""
    global _TOOL_NAME_TO_CATEGORY, _TOOL_BY_NAME
    for category, tools in BUILTIN_TOOLS.items():
        for tool in tools:
            name = tool.get("name")
            if name:
                _TOOL_NAME_TO_CATEGORY[name] = category
                _TOOL_BY_NAME[name] = tool

def get_all_tools() -> List[Dict[str, Any]]:
    """
    Get all built-in tools as a flat list.
    
    Returns:
        List of all tool definitions
    """
    all_tools = []
    for tools in BUILTIN_TOOLS.values():
        all_tools.extend(tools)
    return all_tools

def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a tool definition by name.
    
    Args:
        name: Tool name
        
    Returns:
        Tool definition dict or None if not found
    """
    if not _TOOL_BY_NAME:
        _build_indexes()
    return _TOOL_BY_NAME.get(name)

def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all tools in a category.
    
    Args:
        category: Category name (e.g., "memory", "runtime", "chat", "web", "vm", "mobile")
        
    Returns:
        List of tool definitions in that category
    """
    return BUILTIN_TOOLS.get(category, [])

def get_tool_category(tool_name: str) -> Optional[str]:
    """
    Get the category of a tool by its name.
    
    Args:
        tool_name: Tool name
        
    Returns:
        Category name or None if not found
    """
    if not _TOOL_NAME_TO_CATEGORY:
        _build_indexes()
    return _TOOL_NAME_TO_CATEGORY.get(tool_name)

def get_tool_count() -> Dict[str, int]:
    """Get tool count by category."""
    return {cat: len(tools) for cat, tools in BUILTIN_TOOLS.items() if tools}

def format_tools_for_openai() -> List[Dict[str, Any]]:
    """
    Format all tools for OpenAI function calling API.
    
    Returns:
        List of tools in OpenAI format
    """
    tools = []
    for tool in get_all_tools():
        # Convert inputSchema to parameters
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
        }
        tools.append(openai_tool)
    return tools

def get_stats() -> Dict[str, Any]:
    """
    Get comprehensive statistics about the tool set.
    
    Returns:
        Dict with statistics
    """
    return {
        "total": sum(len(tools) for tools in BUILTIN_TOOLS.values()),
        "by_category": get_tool_count(),
        "categories": list(BUILTIN_TOOLS.keys()),
    }


# Build indexes on module import
_build_indexes()
