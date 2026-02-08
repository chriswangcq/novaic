"""
Skill Repository

Data access layer for skills and agent_skills tables.
Manages reusable capability bundles (prompt + tools + workflow).

Supports:
- Builtin skills: loaded from SKILL.md files, read-only
- Custom skills: user-created, fully editable
- Fork: create editable copy of builtin skill
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# Default keywords for auto-matching builtin skills
BUILTIN_SKILL_KEYWORDS = {
    "desktop": ["screenshot", "click", "mouse", "keyboard", "screen", "gui", "桌面", "截图", "点击", "窗口", "应用"],
    "browser": ["browser", "web", "navigate", "url", "page", "网页", "浏览器", "网站", "链接"],
    "shell": ["command", "shell", "terminal", "bash", "run", "命令", "终端", "执行"],
    "files": ["file", "read", "write", "save", "文件", "读取", "写入", "保存", "目录"],
    "wechat": ["wechat", "微信", "聊天", "消息", "发送"],
    "software": ["app", "application", "launch", "open", "软件", "应用", "打开", "启动"],
    "windows": ["windows", "win", "窗口管理", "任务栏"],
    "context": ["context", "上下文", "环境"],
    "vm-setup": ["setup", "安装", "配置", "初始化"],
    "agent-bootstrap": ["bootstrap", "启动", "初始化"],
}


class SkillRepository:
    """Repository for skills and agent_skills tables."""
    
    def __init__(self, db):
        self.db = db
        self._builtin_skills_dir = self._find_builtin_skills_dir()
    
    def _find_builtin_skills_dir(self) -> Optional[Path]:
        """Find the builtin skills directory."""
        # Try relative to this file first
        base = Path(__file__).parent.parent.parent.parent  # novaic-backend
        skills_dir = base / "mcp_client" / "skills"
        if skills_dir.exists():
            return skills_dir
        return None
    
    # ---------- Builtin Skills Loading ----------
    
    def load_builtin_skills(self) -> List[Dict[str, Any]]:
        """Load all builtin skills from SKILL.md files."""
        if not self._builtin_skills_dir:
            return []
        
        skills = []
        for skill_dir in self._builtin_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            skill = self._parse_skill_md(skill_file, skill_dir.name)
            if skill:
                skills.append(skill)
        
        return skills
    
    def _parse_skill_md(self, path: Path, builtin_id: str) -> Optional[Dict[str, Any]]:
        """Parse a SKILL.md file into a skill dict."""
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None
        
        # Parse YAML frontmatter
        frontmatter = {}
        body = content
        
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
                body = parts[2].strip()
        
        name = frontmatter.get("name", builtin_id)
        description = frontmatter.get("description", "")
        
        # Get keywords for auto-matching
        keywords = BUILTIN_SKILL_KEYWORDS.get(builtin_id, [])
        
        return {
            "id": f"builtin:{builtin_id}",
            "name": name,
            "description": description,
            "prompt": body,  # Full markdown content as prompt
            "tools": [],
            "workflow": "",
            "icon": self._get_icon_for_builtin(builtin_id),
            "enabled": True,
            "source": "builtin",
            "builtin_id": builtin_id,
            "forked_from": None,
            "auto_match_keywords": keywords,
            "created_at": None,
            "updated_at": None,
        }
    
    def _get_icon_for_builtin(self, builtin_id: str) -> str:
        """Get icon for builtin skill."""
        icons = {
            "desktop": "monitor",
            "browser": "globe",
            "shell": "terminal",
            "files": "folder",
            "wechat": "message-circle",
            "software": "package",
            "windows": "layout",
            "context": "info",
            "vm-setup": "settings",
            "agent-bootstrap": "play",
        }
        return icons.get(builtin_id, "zap")
    
    def get_builtin_skill(self, builtin_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific builtin skill by its builtin_id."""
        if not self._builtin_skills_dir:
            return None
        
        skill_dir = self._builtin_skills_dir / builtin_id
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return None
        
        return self._parse_skill_md(skill_file, builtin_id)
    
    # ---------- Skills CRUD ----------
    
    def list_all(self, include_builtin: bool = True) -> List[Dict[str, Any]]:
        """List all skills (custom + optionally builtin)."""
        # Get custom skills from database
        rows = self.db.fetchall(
            "SELECT * FROM skills ORDER BY created_at DESC"
        )
        custom_skills = [self._row_to_dict(row) for row in rows]
        
        if not include_builtin:
            return custom_skills
        
        # Get builtin skills
        builtin_skills = self.load_builtin_skills()
        
        # Merge: builtin first, then custom
        return builtin_skills + custom_skills
    
    def get_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a skill by ID (supports builtin:xxx format)."""
        # Check if it's a builtin skill
        if skill_id.startswith("builtin:"):
            builtin_id = skill_id[8:]  # Remove "builtin:" prefix
            return self.get_builtin_skill(builtin_id)
        
        # Otherwise, get from database
        row = self.db.fetchone(
            "SELECT * FROM skills WHERE id = ?",
            (skill_id,)
        )
        return self._row_to_dict(row) if row else None
    
    def create(
        self,
        name: str,
        description: str = "",
        prompt: str = "",
        tools: Optional[List[str]] = None,
        workflow: str = "",
        icon: str = "zap",
        source: str = "custom",
        builtin_id: Optional[str] = None,
        forked_from: Optional[str] = None,
        auto_match_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new skill."""
        skill_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        tools_json = json.dumps(tools or [], ensure_ascii=False)
        keywords_json = json.dumps(auto_match_keywords or [], ensure_ascii=False)
        
        with self.db.transaction(lock_type="global"):
            self.db.execute(
                """INSERT INTO skills (id, name, description, prompt, tools, workflow, icon, enabled, source, builtin_id, forked_from, auto_match_keywords, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)""",
                (skill_id, name, description, prompt, tools_json, workflow, icon, source, builtin_id, forked_from, keywords_json, now, now)
            )
        
        return self.get_by_id(skill_id) or {"id": skill_id, "name": name}
    
    def fork_builtin(self, builtin_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """Fork a builtin skill to create an editable custom copy."""
        # Get the builtin skill
        builtin_skill = self.get_builtin_skill(builtin_id)
        if not builtin_skill:
            raise ValueError(f"Builtin skill not found: {builtin_id}")
        
        # Create a custom copy
        return self.create(
            name=new_name or f"{builtin_skill['name']} (Custom)",
            description=builtin_skill["description"],
            prompt=builtin_skill["prompt"],
            tools=builtin_skill.get("tools", []),
            workflow=builtin_skill.get("workflow", ""),
            icon=builtin_skill.get("icon", "zap"),
            source="custom",
            forked_from=f"builtin:{builtin_id}",
            auto_match_keywords=builtin_skill.get("auto_match_keywords", []),
        )
    
    def update(
        self,
        skill_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        tools: Optional[List[str]] = None,
        workflow: Optional[str] = None,
        icon: Optional[str] = None,
        enabled: Optional[bool] = None,
        auto_match_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update a skill. Builtin skills cannot be updated."""
        # Check if it's a builtin skill
        if skill_id.startswith("builtin:"):
            raise ValueError("Cannot update builtin skills. Fork it first to create an editable copy.")
        
        now = datetime.utcnow().isoformat()
        updates = ["updated_at = ?"]
        params: list = [now]
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if prompt is not None:
            updates.append("prompt = ?")
            params.append(prompt)
        if tools is not None:
            updates.append("tools = ?")
            params.append(json.dumps(tools, ensure_ascii=False))
        if workflow is not None:
            updates.append("workflow = ?")
            params.append(workflow)
        if icon is not None:
            updates.append("icon = ?")
            params.append(icon)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if auto_match_keywords is not None:
            updates.append("auto_match_keywords = ?")
            params.append(json.dumps(auto_match_keywords, ensure_ascii=False))
        
        set_clause = ", ".join(updates)
        params.append(skill_id)
        
        with self.db.transaction(lock_type="global"):
            self.db.execute(
                f"UPDATE skills SET {set_clause} WHERE id = ?",
                tuple(params)
            )
        
        return self.get_by_id(skill_id) or {"id": skill_id, "success": True}
    
    def delete(self, skill_id: str) -> Dict[str, Any]:
        """Delete a skill (cascades to agent_skills). Builtin skills cannot be deleted."""
        if skill_id.startswith("builtin:"):
            raise ValueError("Cannot delete builtin skills.")
        
        with self.db.transaction(lock_type="global"):
            self.db.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        return {"success": True, "id": skill_id}
    
    # ---------- Agent-Skill Assignments ----------
    
    def get_agent_skills(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all skills assigned to an agent (supports both builtin and custom skills)."""
        # Get all assigned skill IDs with priority
        rows = self.db.fetchall(
            """SELECT skill_id, priority FROM agent_skills
               WHERE agent_id = ?
               ORDER BY priority""",
            (agent_id,)
        )
        
        # Load builtin skills for reference
        builtin_skills = {s["id"]: s for s in self.load_builtin_skills()}
        
        result = []
        for row in rows:
            skill_id = row["skill_id"]
            priority = row["priority"]
            
            if skill_id.startswith("builtin:"):
                # Builtin skill - get from loaded builtin skills
                if skill_id in builtin_skills:
                    skill = builtin_skills[skill_id].copy()
                    skill["priority"] = priority
                    result.append(skill)
            else:
                # Custom skill - get from database
                skill_row = self.db.fetchone(
                    "SELECT * FROM skills WHERE id = ?",
                    (skill_id,)
                )
                if skill_row:
                    skill = self._row_to_dict(skill_row)
                    skill["priority"] = priority
                    result.append(skill)
        
        return result
    
    def set_agent_skills(self, agent_id: str, skill_ids: List[str]) -> Dict[str, Any]:
        """Set the skills for an agent (replace all). Supports both builtin and custom skill IDs."""
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            # Delete existing assignments
            self.db.execute(
                "DELETE FROM agent_skills WHERE agent_id = ?",
                (agent_id,)
            )
            
            # Insert new assignments (no FK constraint check for builtin skills)
            now = datetime.utcnow().isoformat()
            inserted_count = 0
            for i, skill_id in enumerate(skill_ids):
                # Validate skill exists (either builtin or custom)
                if skill_id.startswith("builtin:"):
                    # Builtin skill - always valid if it exists in our builtin list
                    builtin_id = skill_id.replace("builtin:", "")
                    builtin_skills = self.load_builtin_skills()
                    if not any(s["builtin_id"] == builtin_id for s in builtin_skills):
                        continue  # Skip invalid builtin skill
                else:
                    # Custom skill - check if exists in database
                    exists = self.db.fetchone(
                        "SELECT 1 FROM skills WHERE id = ?",
                        (skill_id,)
                    )
                    if not exists:
                        continue  # Skip invalid custom skill
                
                # Insert without FK constraint (agent_skills.skill_id is just TEXT)
                self.db.execute(
                    """INSERT OR REPLACE INTO agent_skills (agent_id, skill_id, priority, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (agent_id, skill_id, i, now)
                )
                inserted_count += 1
        
        return {"success": True, "count": inserted_count}
    
    # ---------- Auto-matching Skills ----------
    
    def match_skills_for_task(self, task: str, max_skills: int = 3) -> List[Dict[str, Any]]:
        """
        Match skills based on task description using keywords.
        Returns the most relevant skills for the given task.
        """
        task_lower = task.lower()
        all_skills = self.list_all(include_builtin=True)
        
        matched = []
        for skill in all_skills:
            keywords = skill.get("auto_match_keywords", [])
            if not keywords:
                continue
            
            # Check if any keyword matches
            if any(kw.lower() in task_lower for kw in keywords):
                matched.append(skill)
                if len(matched) >= max_skills:
                    break
        
        # If no match, return desktop skill as default (for GUI tasks)
        if not matched:
            desktop_skill = self.get_builtin_skill("desktop")
            if desktop_skill:
                matched.append(desktop_skill)
        
        return matched
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        # Get column names from the row
        try:
            columns = row.keys() if hasattr(row, 'keys') else []
        except Exception:
            columns = []
        
        result = {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"] or "",
            "prompt": row["prompt"] or "",
            "tools": json.loads(row["tools"] or "[]"),
            "workflow": row["workflow"] or "",
            "icon": row["icon"] or "zap",
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        
        # Add new fields - use try/except for compatibility with old schema
        try:
            result["source"] = row["source"] or "custom"
        except (KeyError, IndexError):
            result["source"] = "custom"
        
        try:
            result["builtin_id"] = row["builtin_id"]
        except (KeyError, IndexError):
            result["builtin_id"] = None
        
        try:
            result["forked_from"] = row["forked_from"]
        except (KeyError, IndexError):
            result["forked_from"] = None
        
        try:
            result["auto_match_keywords"] = json.loads(row["auto_match_keywords"] or "[]")
        except (KeyError, IndexError):
            result["auto_match_keywords"] = []
        
        return result
