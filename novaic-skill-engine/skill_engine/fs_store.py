"""
Skill Engine — File System Skill Store (文件系统技能存储)

Scans workspace directories for SKILL.md files, parses YAML frontmatter
and markdown body, and provides them as SkillMetadata/SkillBody.

Multi-root scan order (Claude Code aligned):
  1. Bundled skills (system builtin directory)
  2. User global skills (~/.novaic/skills/)
  3. Workspace skills (<workspace>/.agents/skills/)
  4. Workspace root skills (<workspace>/skills/)

Same‐name skills: later root **overrides** earlier root (workspace > user > builtin).

Each SKILL.md is expected to have YAML frontmatter:
  ---
  name: my-skill
  description: What this skill does
  when_to_use: When to activate
  keywords: [python, debugging]
  paths: ["src/**/*.py"]
  arguments: [ARG1, ARG2]
  priority: 0
  ---
  <markdown body = the skill prompt>
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from .types import (
    Skill,
    SkillBody,
    SkillMetadata,
    SkillReference,
    SkillSource,
)

logger = logging.getLogger("skill_engine.fs_store")

# ── YAML frontmatter regex ──
# Matches:  ---\n<yaml>\n---\n<body>
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n(.*)$",
    re.DOTALL,
)


class FileSystemSkillStore:
    """
    SkillStore implementation that scans file system directories for SKILL.md files.

    Usage:
        store = FileSystemSkillStore(
            roots=[
                "/app/builtin_skills",
                "~/.novaic/skills",
                "/project/.agents/skills",
            ]
        )
        metadata_list = store.list_metadata()
        body = store.load_body("skill-id")

    Features:
        - Multi-root scanning with override semantics (last wins)
        - YAML frontmatter parsing (no PyYAML dependency — simple parser)
        - Lazy body loading (metadata is always loaded, body on demand)
        - Stable ID generation from skill path for dedup
    """

    def __init__(
        self,
        roots: Optional[List[str]] = None,
        workspace: Optional[str] = None,
        user_home: Optional[str] = None,
    ):
        """
        Args:
            roots: explicit list of directories to scan (overrides auto-detection)
            workspace: workspace root path (auto-detects .agents/skills, skills/)
            user_home: user home directory (auto-detects ~/.novaic/skills/)
        """
        self._skills: Dict[str, _SkillEntry] = {}  # id → entry
        self._by_name: Dict[str, str] = {}  # name → id

        if roots:
            self._roots = [os.path.expanduser(r) for r in roots]
        else:
            self._roots = self._auto_detect_roots(workspace, user_home)

    @staticmethod
    def _auto_detect_roots(
        workspace: Optional[str] = None,
        user_home: Optional[str] = None,
    ) -> List[str]:
        """Build default scan roots."""
        roots = []
        home = user_home or os.path.expanduser("~")

        # User global skills
        user_skills = os.path.join(home, ".novaic", "skills")
        if os.path.isdir(user_skills):
            roots.append(user_skills)

        # Workspace skills
        if workspace:
            for subdir in (".agents/skills", ".agent/skills", "skills"):
                path = os.path.join(workspace, subdir)
                if os.path.isdir(path):
                    roots.append(path)

        return roots

    # ── SkillStore Protocol ──

    def list_metadata(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[SkillMetadata]:
        """Scan all roots and return metadata for discovered skills."""
        self._scan()
        return [entry.metadata for entry in self._skills.values()]

    def load_body(self, skill_id: str) -> Optional[SkillBody]:
        """Load skill body (markdown content below frontmatter)."""
        entry = self._skills.get(skill_id)
        if not entry:
            return None
        if entry.body is not None:
            return entry.body

        # Lazy load
        body = self._parse_body(entry.path)
        entry.body = body
        return body

    def load_references(self, skill_id: str) -> List[SkillReference]:
        """Load referenced files from the skill directory."""
        entry = self._skills.get(skill_id)
        if not entry:
            return []

        skill_dir = os.path.dirname(entry.path)
        refs = []

        for fname in os.listdir(skill_dir):
            fpath = os.path.join(skill_dir, fname)
            if fname == "SKILL.md" or not os.path.isfile(fpath):
                continue
            # Skip hidden files and large files
            if fname.startswith(".") or os.path.getsize(fpath) > 50_000:
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                refs.append(SkillReference(
                    path=fpath,
                    content=content,
                    token_estimate=max(1, len(content) // 4),
                ))
            except Exception as e:
                logger.debug("Skip reference %s: %s", fpath, e)

        return refs

    def get_agent_skills(self, agent_id: str) -> List[str]:
        """File system store does not support agent binding."""
        return []

    # ── Scanning ──

    def _scan(self) -> None:
        """Scan all roots for SKILL.md files. Later roots override earlier."""
        self._skills.clear()
        self._by_name.clear()

        for root in self._roots:
            if not os.path.isdir(root):
                continue
            self._scan_root(root)

        logger.info(
            "[FileSystemSkillStore] Scanned %d roots, found %d skills",
            len(self._roots), len(self._skills),
        )

    def _scan_root(self, root: str) -> None:
        """Scan a single root directory for skills."""
        root_path = Path(root)

        # Pattern 1: <root>/<skill_name>/SKILL.md
        for child in sorted(root_path.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            skill_md = child / "SKILL.md"
            if skill_md.is_file():
                self._load_skill_file(str(skill_md), root)

        # Pattern 2: <root>/SKILL.md (single skill at root)
        root_skill = root_path / "SKILL.md"
        if root_skill.is_file():
            self._load_skill_file(str(root_skill), root)

    def _load_skill_file(self, path: str, root: str) -> None:
        """Parse a single SKILL.md and register it."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.warning("Failed to read %s: %s", path, e)
            return

        frontmatter = self._parse_frontmatter(content)
        if not frontmatter:
            logger.warning("No valid frontmatter in %s", path)
            return

        name = frontmatter.get("name", "")
        if not name:
            # Derive name from directory
            name = os.path.basename(os.path.dirname(path))
            if name == os.path.basename(root):
                name = os.path.basename(path).replace(".md", "")

        # Generate stable ID from path
        skill_id = self._make_id(path)

        # Determine source
        source = SkillSource.BUILTIN
        if "/.novaic/" in path or "/.agents/" in path or "/.agent/" in path:
            source = SkillSource.CUSTOM

        metadata = SkillMetadata(
            id=skill_id,
            name=name,
            description=frontmatter.get("description", ""),
            when_to_use=frontmatter.get("when_to_use", ""),
            source=source,
            keywords=self._parse_list(frontmatter.get("keywords")),
            paths=self._parse_list(frontmatter.get("paths")),
            version=str(frontmatter.get("version", "")),
            priority=int(frontmatter.get("priority", 0)),
        )

        entry = _SkillEntry(
            metadata=metadata,
            path=path,
            root=root,
            body=None,
        )

        # Later roots override earlier (by name)
        if name in self._by_name:
            old_id = self._by_name[name]
            del self._skills[old_id]
            logger.debug("Skill '%s' overridden by %s", name, path)

        self._skills[skill_id] = entry
        self._by_name[name] = skill_id

    # ── Parsing ──

    @staticmethod
    def _parse_frontmatter(content: str) -> Optional[Dict]:
        """
        Parse YAML frontmatter without PyYAML dependency.

        Handles simple key: value pairs, lists with [] or - syntax.
        """
        match = _FRONTMATTER_RE.match(content)
        if not match:
            return None

        yaml_text = match.group(1)
        result = {}

        for line in yaml_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" not in line:
                continue

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            # Handle YAML list syntax [item1, item2]
            if value.startswith("[") and value.endswith("]"):
                items = value[1:-1].split(",")
                result[key] = [
                    item.strip().strip("'\"")
                    for item in items
                    if item.strip()
                ]
            elif value.startswith("'") or value.startswith('"'):
                result[key] = value.strip("'\"")
            else:
                result[key] = value

        return result

    def _parse_body(self, path: str) -> Optional[SkillBody]:
        """Parse the markdown body (below frontmatter) from a SKILL.md."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None

        match = _FRONTMATTER_RE.match(content)
        if not match:
            return SkillBody(prompt=content)

        body_text = match.group(2).strip()
        if not body_text:
            return SkillBody()

        # Extract workflow section if present
        workflow = ""
        prompt = body_text

        workflow_match = re.search(
            r"##?\s*(?:Workflow|工作流|Steps)\s*\n(.+?)(?=\n##?\s|\Z)",
            body_text,
            re.DOTALL | re.IGNORECASE,
        )
        if workflow_match:
            workflow = workflow_match.group(1).strip()
            prompt = body_text[:workflow_match.start()].strip()
            # Append anything after the workflow section
            after = body_text[workflow_match.end():].strip()
            if after:
                prompt += "\n\n" + after

        # Extract allowed_tools if present
        allowed_tools = []
        tools_match = re.search(
            r"##?\s*(?:Allowed Tools|允许的工具)\s*\n(.+?)(?=\n##?\s|\Z)",
            body_text,
            re.DOTALL | re.IGNORECASE,
        )
        if tools_match:
            tools_text = tools_match.group(1)
            allowed_tools = [
                t.strip().lstrip("- ")
                for t in tools_text.split("\n")
                if t.strip() and t.strip() != "-"
            ]

        # Extract arguments from frontmatter
        frontmatter = self._parse_frontmatter(
            open(path, "r", encoding="utf-8").read()
        )
        arguments = self._parse_list(
            frontmatter.get("arguments") if frontmatter else None
        )

        return SkillBody(
            prompt=prompt,
            workflow=workflow,
            allowed_tools=allowed_tools,
            arguments=arguments,
        )

    @staticmethod
    def _parse_list(value) -> List[str]:
        """Normalize a value to a list of strings."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if v]
        if isinstance(value, str):
            if value.startswith("["):
                # Already parsed by frontmatter parser
                return []
            return [v.strip() for v in value.split(",") if v.strip()]
        return []

    @staticmethod
    def _make_id(path: str) -> str:
        """Generate a stable, deterministic skill ID from file path."""
        h = hashlib.md5(path.encode()).hexdigest()[:8]
        name = os.path.basename(os.path.dirname(path))
        return f"fs:{name}:{h}"

    # ── Utility ──

    @property
    def roots(self) -> List[str]:
        """Return configured scan roots."""
        return list(self._roots)

    @property
    def skill_count(self) -> int:
        return len(self._skills)

    def add_root(self, root: str) -> None:
        """Add a new scan root."""
        expanded = os.path.expanduser(root)
        if expanded not in self._roots:
            self._roots.append(expanded)


class _SkillEntry:
    """Internal storage for a discovered skill."""
    __slots__ = ("metadata", "path", "root", "body")

    def __init__(
        self,
        metadata: SkillMetadata,
        path: str,
        root: str,
        body: Optional[SkillBody],
    ):
        self.metadata = metadata
        self.path = path
        self.root = root
        self.body = body
