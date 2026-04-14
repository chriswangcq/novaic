"""
Skill Repository — business-owned data access for skills.

Manages builtin (SKILL.md) + custom skills + agent-skill assignments.
All CRUD goes through BusinessEntityStore (Entangled HTTP).
"""

import uuid
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any

from common.utils.time import utc_now_iso
from business.entity_store import get_entity_store

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

BUILTIN_ICONS = {
    "desktop": "monitor", "browser": "globe", "shell": "terminal",
    "files": "folder", "wechat": "message-circle", "software": "package",
    "windows": "layout", "context": "info", "vm-setup": "settings",
    "agent-bootstrap": "play",
}

logger = logging.getLogger(__name__)


class SkillRepository:
    """Skills data access — backed by Entangled via BusinessEntityStore."""

    def __init__(self):
        self._builtin_skills_dir = self._find_builtin_skills_dir()

    @staticmethod
    def _find_builtin_skills_dir() -> Optional[Path]:
        from common.config import ServiceConfig
        skills_dir = ServiceConfig.SKILLS_DIR
        if skills_dir:
            p = Path(skills_dir)
            if p.exists():
                return p

        data_dir = getattr(ServiceConfig, "DATA_DIR", "")
        if data_dir:
            p = Path(data_dir) / "skills"
            if p.exists():
                return p

        base = Path(__file__).parent.parent.parent  # workspace root
        p = base / "mcp_client" / "skills"
        if p.exists():
            return p
        return None

    # ── Builtin Skills ────────────────────────────────────────────────────────

    def load_builtin_skills(self) -> List[Dict[str, Any]]:
        if not self._builtin_skills_dir:
            return []
        skills = []
        for skill_dir in self._builtin_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skill = self._parse_skill_md(skill_file, skill_dir.name)
                if skill:
                    skills.append(skill)
        return skills

    def _parse_skill_md(self, path: Path, builtin_id: str) -> Optional[Dict[str, Any]]:
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

        frontmatter, body = {}, content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import yaml
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
                body = parts[2].strip()

        return {
            "id": f"builtin:{builtin_id}",
            "name": frontmatter.get("name", builtin_id),
            "description": frontmatter.get("description", ""),
            "prompt": body,
            "tools": [], "workflow": "",
            "icon": BUILTIN_ICONS.get(builtin_id, "zap"),
            "enabled": True, "source": "builtin",
            "builtin_id": builtin_id, "forked_from": None,
            "auto_match_keywords": BUILTIN_SKILL_KEYWORDS.get(builtin_id, []),
            "created_at": None, "updated_at": None,
        }

    def get_builtin_skill(self, builtin_id: str) -> Optional[Dict[str, Any]]:
        if not self._builtin_skills_dir:
            return None
        skill_file = self._builtin_skills_dir / builtin_id / "SKILL.md"
        return self._parse_skill_md(skill_file, builtin_id) if skill_file.exists() else None

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list_all(self, user_id: str, include_builtin: bool = True) -> List[Dict[str, Any]]:
        store = get_entity_store()
        custom = store.list("skills", user_id, order_by="created_at DESC")
        if not include_builtin:
            return custom
        return self.load_builtin_skills() + custom

    def get_by_id(self, skill_id: str, user_id: str = "") -> Optional[Dict[str, Any]]:
        if skill_id.startswith("builtin:"):
            return self.get_builtin_skill(skill_id[8:])
        return get_entity_store().get("skills", user_id, skill_id)

    def create(self, name: str, user_id: str, **kw) -> Dict[str, Any]:
        data = {
            "id": str(uuid.uuid4()), "name": name,
            "description": kw.get("description", ""),
            "prompt": kw.get("prompt", ""),
            "tools": kw.get("tools") or [],
            "workflow": kw.get("workflow", ""),
            "icon": kw.get("icon", "zap"),
            "enabled": True,
            "source": kw.get("source", "custom"),
            "builtin_id": kw.get("builtin_id"),
            "forked_from": kw.get("forked_from"),
            "auto_match_keywords": kw.get("auto_match_keywords") or [],
        }
        return get_entity_store().create("skills", user_id, data)

    def fork_builtin(self, builtin_id: str, user_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        builtin = self.get_builtin_skill(builtin_id)
        if not builtin:
            raise ValueError(f"Builtin skill not found: {builtin_id}")
        return self.create(
            name=new_name or f"{builtin['name']} (Custom)", user_id=user_id,
            description=builtin["description"], prompt=builtin["prompt"],
            tools=builtin.get("tools", []), workflow=builtin.get("workflow", ""),
            icon=builtin.get("icon", "zap"), source="custom",
            forked_from=f"builtin:{builtin_id}",
            auto_match_keywords=builtin.get("auto_match_keywords", []),
        )

    def update(self, skill_id: str, user_id: str, **kw) -> Dict[str, Any]:
        if skill_id.startswith("builtin:"):
            raise ValueError("Cannot update builtin skills. Fork it first.")
        data = {k: v for k, v in kw.items() if v is not None}
        if not data:
            return self.get_by_id(skill_id, user_id) or {"id": skill_id}
        return get_entity_store().update("skills", user_id, skill_id, data)

    def delete(self, skill_id: str, user_id: str) -> Dict[str, Any]:
        if skill_id.startswith("builtin:"):
            raise ValueError("Cannot delete builtin skills.")
        get_entity_store().delete("skills", user_id, skill_id)
        return {"success": True, "id": skill_id}

    # ── Agent-Skill Assignments ───────────────────────────────────────────────

    def get_agent_skills(self, agent_id: str, user_id: str = "") -> List[Dict[str, Any]]:
        store = get_entity_store()
        assignments = store.list("agent-skills", "", params={"agent_id": agent_id}, order_by="priority ASC")
        builtins = {s["id"]: s for s in self.load_builtin_skills()}
        result = []
        for a in assignments:
            sid, pri = a["skill_id"], a.get("priority", 0)
            if sid.startswith("builtin:") and sid in builtins:
                s = builtins[sid].copy(); s["priority"] = pri; result.append(s)
            elif not sid.startswith("builtin:"):
                s = store.get("skills", user_id, sid)
                if s:
                    s = dict(s); s["priority"] = pri; result.append(s)
        return result

    def set_agent_skills(self, agent_id: str, skill_ids: List[str], user_id: str) -> Dict[str, Any]:
        store = get_entity_store()
        store.delete_where("agent-skills", "", params={"agent_id": agent_id})
        now, count = utc_now_iso(), 0
        for i, sid in enumerate(skill_ids):
            if sid.startswith("builtin:"):
                if not any(s["builtin_id"] == sid.replace("builtin:", "") for s in self.load_builtin_skills()):
                    continue
            else:
                if not store.get("skills", user_id, sid):
                    continue
            store.create("agent-skills", "", {"agent_id": agent_id, "skill_id": sid, "priority": i, "created_at": now})
            count += 1
        return {"success": True, "count": count}

    # ── Matching ──────────────────────────────────────────────────────────────

    def match_skills_for_task(self, task: str, user_id: str, max_skills: int = 3) -> List[Dict[str, Any]]:
        task_lower = task.lower()
        matched = []
        for skill in self.list_all(user_id=user_id, include_builtin=True):
            kws = skill.get("auto_match_keywords", [])
            if kws and any(kw.lower() in task_lower for kw in kws):
                matched.append(skill)
                if len(matched) >= max_skills:
                    break
        if not matched:
            desktop = self.get_builtin_skill("desktop")
            if desktop:
                matched.append(desktop)
        return matched
