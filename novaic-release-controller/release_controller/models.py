"""Typed domain models for the NovAIC release controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class ReleaseMode(str, Enum):
    """How a matched branch should be handled."""

    AUTO_DEPLOY = "auto_deploy"
    CANDIDATE_ONLY = "candidate_only"


class RunStatus(str, Enum):
    """Release run lifecycle states."""

    QUEUED = "queued"
    PLANNING = "planning"
    VERIFYING = "verifying"
    BUILDING = "building"
    PUBLISHING = "publishing"
    DEPLOYING = "deploying"
    SMOKE_TESTING = "smoke_testing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"

    @property
    def is_terminal(self) -> bool:
        return self in {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.SKIPPED}


class TriggerKind(str, Enum):
    """Source that started a release run."""

    POLL = "poll"
    MANUAL = "manual"
    PROMOTION = "promotion"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class BranchRule:
    """A branch pattern and the release behavior it allows."""

    pattern: str
    mode: ReleaseMode
    namespace: str | None = None
    namespace_template: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "BranchRule":
        pattern = _required_str(data, "pattern")
        mode = ReleaseMode(_required_str(data, "mode"))
        namespace = _optional_str(data, "namespace")
        namespace_template = _optional_str(data, "namespace_template")
        rule = cls(
            pattern=pattern,
            mode=mode,
            namespace=namespace,
            namespace_template=namespace_template,
        )
        rule.validate()
        return rule

    def validate(self) -> None:
        if self.mode is ReleaseMode.AUTO_DEPLOY:
            if not self.namespace and not self.namespace_template:
                raise ValueError(f"auto_deploy rule {self.pattern!r} needs a namespace")
            if self.namespace == "prod":
                raise ValueError("prod cannot be an automatic branch deployment target")
        if self.mode is ReleaseMode.CANDIDATE_ONLY and self.namespace == "prod":
            raise ValueError("release candidate rules must not target prod directly")

    def to_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "pattern": self.pattern,
            "mode": self.mode.value,
        }
        if self.namespace is not None:
            data["namespace"] = self.namespace
        if self.namespace_template is not None:
            data["namespace_template"] = self.namespace_template
        return data


@dataclass(frozen=True)
class RepoConfig:
    """Git repository settings used by the controller."""

    path: str | None = None
    url: str | None = None
    remote: str = "origin"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RepoConfig":
        path = _optional_str(data, "path")
        url = _optional_str(data, "url")
        remote = _optional_str(data, "remote") or "origin"
        if not path and not url:
            raise ValueError("repo.path or repo.url is required")
        return cls(path=path, url=url, remote=remote)

    def to_mapping(self) -> dict[str, Any]:
        data = {"remote": self.remote}
        if self.path is not None:
            data["path"] = self.path
        if self.url is not None:
            data["url"] = self.url
        return data


@dataclass(frozen=True)
class RegistryConfig:
    """Container image repository settings."""

    api_image: str
    factory_image: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RegistryConfig":
        return cls(
            api_image=_required_str(data, "api_image"),
            factory_image=_required_str(data, "factory_image"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "api_image": self.api_image,
            "factory_image": self.factory_image,
        }


@dataclass(frozen=True)
class DeployConfig:
    """Deployment command settings."""

    script_path: str
    verify_commands: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    health_urls: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DeployConfig":
        return cls(
            script_path=_required_str(data, "script_path"),
            verify_commands=_command_list(data.get("verify_commands", [])),
            health_urls=_str_mapping(data.get("health_urls", {}), "deploy.health_urls"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "script_path": self.script_path,
            "verify_commands": [list(command) for command in self.verify_commands],
            "health_urls": dict(self.health_urls),
        }


@dataclass(frozen=True)
class ServerConfig:
    """HTTP server bind settings."""

    host: str = "127.0.0.1"
    port: int = 19880

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "ServerConfig":
        if data is None:
            return cls()
        host = _optional_str(data, "host") or "127.0.0.1"
        port_value = data.get("port", 19880)
        if not isinstance(port_value, int) or not 1 <= port_value <= 65535:
            raise ValueError("server.port must be an integer between 1 and 65535")
        return cls(host=host, port=port_value)

    def to_mapping(self) -> dict[str, Any]:
        return {"host": self.host, "port": self.port}


@dataclass(frozen=True)
class ControllerConfig:
    """Complete release-controller configuration."""

    state_dir: str
    repo: RepoConfig
    registry: RegistryConfig
    deploy: DeployConfig
    branch_rules: tuple[BranchRule, ...]
    poll_interval_seconds: int = 60
    polling_enabled: bool = False
    dry_run_default: bool = True
    server: ServerConfig = field(default_factory=ServerConfig)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ControllerConfig":
        state_dir = _required_str(data, "state_dir")
        branch_rules = _branch_rules(data.get("branch_rules"))
        poll_interval = data.get("poll_interval_seconds", 60)
        if not isinstance(poll_interval, int) or poll_interval <= 0:
            raise ValueError("poll_interval_seconds must be a positive integer")
        polling_enabled = data.get("polling_enabled", False)
        if not isinstance(polling_enabled, bool):
            raise ValueError("polling_enabled must be a boolean")
        dry_run_default = data.get("dry_run_default", True)
        if not isinstance(dry_run_default, bool):
            raise ValueError("dry_run_default must be a boolean")
        return cls(
            state_dir=state_dir,
            repo=RepoConfig.from_mapping(_required_mapping(data, "repo")),
            registry=RegistryConfig.from_mapping(_required_mapping(data, "registry")),
            deploy=DeployConfig.from_mapping(_required_mapping(data, "deploy")),
            branch_rules=branch_rules,
            poll_interval_seconds=poll_interval,
            polling_enabled=polling_enabled,
            dry_run_default=dry_run_default,
            server=ServerConfig.from_mapping(_optional_mapping(data, "server")),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "state_dir": self.state_dir,
            "repo": self.repo.to_mapping(),
            "registry": self.registry.to_mapping(),
            "deploy": self.deploy.to_mapping(),
            "branch_rules": [rule.to_mapping() for rule in self.branch_rules],
            "poll_interval_seconds": self.poll_interval_seconds,
            "polling_enabled": self.polling_enabled,
            "dry_run_default": self.dry_run_default,
            "server": self.server.to_mapping(),
        }


@dataclass(frozen=True)
class ImageRefs:
    """API and Factory image refs that move together through a release."""

    api_image: str
    factory_image: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ImageRefs":
        return cls(
            api_image=_required_str(data, "api_image"),
            factory_image=_required_str(data, "factory_image"),
        )

    def to_mapping(self) -> dict[str, str]:
        return {"api_image": self.api_image, "factory_image": self.factory_image}


@dataclass(frozen=True)
class CommandStep:
    """One command that may be executed by the controller."""

    name: str
    argv: tuple[str, ...]
    cwd: str | None = None
    env: Mapping[str, str] = field(default_factory=dict)
    sensitive: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CommandStep":
        argv = data.get("argv")
        if not isinstance(argv, Sequence) or isinstance(argv, (str, bytes)):
            raise ValueError("command step argv must be an array")
        command = tuple(str(part) for part in argv)
        if not command:
            raise ValueError("command step argv must not be empty")
        env = _str_mapping(data.get("env", {}), "command step env")
        sensitive = data.get("sensitive", False)
        if not isinstance(sensitive, bool):
            raise ValueError("command step sensitive must be a boolean")
        return cls(
            name=_required_str(data, "name"),
            argv=command,
            cwd=_optional_str(data, "cwd"),
            env=env,
            sensitive=sensitive,
        )

    def to_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "argv": list(self.argv),
            "env": dict(self.env),
            "sensitive": self.sensitive,
        }
        if self.cwd is not None:
            data["cwd"] = self.cwd
        return data


@dataclass(frozen=True)
class CommandPlan:
    """A deterministic command plan for a release action."""

    steps: tuple[CommandStep, ...]
    dry_run: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CommandPlan":
        dry_run = data.get("dry_run")
        if not isinstance(dry_run, bool):
            raise ValueError("command plan dry_run must be a boolean")
        steps = data.get("steps")
        if not isinstance(steps, Sequence) or isinstance(steps, (str, bytes)):
            raise ValueError("command plan steps must be an array")
        return cls(
            dry_run=dry_run,
            steps=tuple(CommandStep.from_mapping(step) for step in steps if isinstance(step, Mapping)),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "steps": [step.to_mapping() for step in self.steps],
        }


@dataclass(frozen=True)
class CommandResult:
    """Captured result for one command step."""

    name: str
    argv: tuple[str, ...]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    skipped: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CommandResult":
        argv = data.get("argv")
        if not isinstance(argv, Sequence) or isinstance(argv, (str, bytes)):
            raise ValueError("command result argv must be an array")
        exit_code = data.get("exit_code")
        if not isinstance(exit_code, int):
            raise ValueError("command result exit_code must be an integer")
        skipped = data.get("skipped", False)
        if not isinstance(skipped, bool):
            raise ValueError("command result skipped must be a boolean")
        return cls(
            name=_required_str(data, "name"),
            argv=tuple(str(part) for part in argv),
            exit_code=exit_code,
            stdout=str(data.get("stdout", "")),
            stderr=str(data.get("stderr", "")),
            skipped=skipped,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "argv": list(self.argv),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "skipped": self.skipped,
        }


@dataclass(frozen=True)
class ReleasePointer:
    """Current, previous, or candidate release pointer."""

    namespace: str
    commit: str
    images: ImageRefs
    run_id: str
    updated_at: str
    promoted_from: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleasePointer":
        return cls(
            namespace=_required_str(data, "namespace"),
            commit=_required_str(data, "commit"),
            images=ImageRefs.from_mapping(data),
            run_id=_required_str(data, "run_id"),
            updated_at=_required_str(data, "updated_at"),
            promoted_from=_optional_str(data, "promoted_from"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "commit": self.commit,
            "api_image": self.images.api_image,
            "factory_image": self.images.factory_image,
            "run_id": self.run_id,
            "promoted_from": self.promoted_from,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ReleaseRun:
    """Persisted record for one release-controller run."""

    run_id: str
    trigger: TriggerKind
    branch: str | None
    commit: str
    status: RunStatus
    namespace: str | None = None
    images: ImageRefs | None = None
    command_plan: CommandPlan | None = None
    failure: str | None = None
    started_at: str | None = None
    finished_at: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ReleaseRun":
        images = None
        if data.get("api_image") is not None or data.get("factory_image") is not None:
            images = ImageRefs.from_mapping(data)
        command_plan = None
        if isinstance(data.get("command_plan"), Mapping):
            command_plan = CommandPlan.from_mapping(data["command_plan"])
        return cls(
            run_id=_required_str(data, "run_id"),
            trigger=TriggerKind(_required_str(data, "trigger")),
            branch=_optional_str(data, "branch"),
            commit=_required_str(data, "commit"),
            namespace=_optional_str(data, "namespace"),
            status=RunStatus(_required_str(data, "status")),
            images=images,
            command_plan=command_plan,
            failure=_optional_str(data, "failure"),
            started_at=_optional_str(data, "started_at"),
            finished_at=_optional_str(data, "finished_at"),
        )

    def to_mapping(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "run_id": self.run_id,
            "trigger": self.trigger.value,
            "branch": self.branch,
            "commit": self.commit,
            "namespace": self.namespace,
            "status": self.status.value,
            "failure": self.failure,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
        if self.images is not None:
            data.update(self.images.to_mapping())
        if self.command_plan is not None:
            data["command_plan"] = self.command_plan.to_mapping()
        return data


def _required_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _optional_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _required_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_str(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string when set")
    return value


def _branch_rules(value: Any) -> tuple[BranchRule, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("branch_rules must be a non-empty array")
    rules = tuple(BranchRule.from_mapping(item) for item in value if isinstance(item, Mapping))
    if len(rules) != len(value) or not rules:
        raise ValueError("branch_rules must contain only rule objects")
    return rules


def _command_list(value: Any) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("verify_commands must be an array of argv arrays")
    commands: list[tuple[str, ...]] = []
    for item in value:
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)):
            raise ValueError("each verify command must be an argv array")
        command = tuple(str(part) for part in item)
        if not command:
            raise ValueError("verify command argv arrays must not be empty")
        commands.append(command)
    return tuple(commands)


def _str_mapping(value: Any, field_name: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not item:
            raise ValueError(f"{field_name} must map strings to non-empty strings")
        result[key] = item
    return result
