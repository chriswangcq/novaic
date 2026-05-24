"""Release planning logic for branch-triggered and manual deployments."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
import re
from typing import Callable

from release_controller.models import (
    BranchRule,
    CommandPlan,
    CommandStep,
    ControllerConfig,
    ImageRefs,
    ReleaseMode,
    ReleaseRun,
    RunStatus,
    TriggerKind,
)
from release_controller.state import ReleaseStateStore

Clock = Callable[[], datetime]

_SHA_TAG_RE = re.compile(r"^sha-[0-9a-fA-F]{7,64}$")
_MUTABLE_TAGS = {"latest", "local", "main", "master", "prod", "production", "staging"}


class PlanningError(ValueError):
    """Raised when a release request violates controller release rules."""


@dataclass(frozen=True)
class PlannedRelease:
    """Planner output shared by API, poller, and tests."""

    run: ReleaseRun
    plan: CommandPlan
    mode: ReleaseMode
    namespace: str | None = None
    candidate_id: str | None = None
    images: ImageRefs | None = None


class ReleasePlanner:
    """Build deterministic command plans from branch rules and release requests."""

    def __init__(
        self,
        config: ControllerConfig,
        state: ReleaseStateStore,
        clock: Clock | None = None,
    ) -> None:
        self.config = config
        self.state = state
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def plan_branch_release(
        self,
        branch: str,
        commit: str,
        trigger: TriggerKind = TriggerKind.MANUAL,
        dry_run: bool | None = None,
    ) -> PlannedRelease:
        rule = self.match_branch_rule(branch)
        short_commit = commit[:12]
        namespace = self.resolve_namespace(rule, branch)
        if namespace == "prod":
            raise PlanningError("branch-triggered releases cannot target prod")
        images = ImageRefs(
            api_image=f"{self.config.registry.api_image}:sha-{short_commit}",
            factory_image=f"{self.config.registry.factory_image}:sha-{short_commit}",
        )
        run_id = self._run_id(branch, commit)
        effective_dry_run = bool(dry_run)
        steps = self._branch_steps(branch, commit, images, namespace, rule.mode, run_id)
        plan = CommandPlan(steps=tuple(steps), dry_run=effective_dry_run)
        candidate_id = None
        if rule.mode is ReleaseMode.CANDIDATE_ONLY:
            candidate_id = f"{_safe_slug(branch)}-{short_commit}"
        run = ReleaseRun(
            run_id=run_id,
            trigger=trigger,
            branch=branch,
            commit=commit,
            namespace=namespace,
            status=RunStatus.PLANNING,
            images=images,
            command_plan=plan,
            started_at=self._now(),
        )
        return PlannedRelease(
            run=run,
            plan=plan,
            mode=rule.mode,
            namespace=namespace,
            candidate_id=candidate_id,
            images=images,
        )

    def plan_prod_promotion(
        self,
        api_image: str,
        factory_image: str,
        commit: str,
        promoted_from: str | None = None,
        dry_run: bool | None = None,
    ) -> PlannedRelease:
        assert_immutable_image_ref(api_image)
        assert_immutable_image_ref(factory_image)
        images = ImageRefs(api_image=api_image, factory_image=factory_image)
        effective_dry_run = bool(dry_run)
        run_id = self._run_id(f"promote-prod-{promoted_from or 'manual'}", commit)
        plan = CommandPlan(
            steps=tuple(self._deploy_steps("prod", images, run_id, commit)),
            dry_run=effective_dry_run,
        )
        run = ReleaseRun(
            run_id=run_id,
            trigger=TriggerKind.PROMOTION,
            branch=None,
            commit=commit,
            namespace="prod",
            status=RunStatus.PLANNING,
            images=images,
            command_plan=plan,
            started_at=self._now(),
        )
        return PlannedRelease(
            run=run,
            plan=plan,
            mode=ReleaseMode.AUTO_DEPLOY,
            namespace="prod",
            images=images,
        )

    def plan_rollback(self, namespace: str, dry_run: bool | None = None) -> PlannedRelease:
        previous = self.state.get_previous_release(namespace)
        if previous is None:
            raise PlanningError(f"no previous release pointer exists for namespace {namespace!r}")
        assert_immutable_image_ref(previous.images.api_image)
        assert_immutable_image_ref(previous.images.factory_image)
        effective_dry_run = bool(dry_run)
        run_id = self._run_id(f"rollback-{namespace}", previous.commit)
        plan = CommandPlan(
            steps=tuple(self._deploy_steps(namespace, previous.images, run_id, previous.commit)),
            dry_run=effective_dry_run,
        )
        run = ReleaseRun(
            run_id=run_id,
            trigger=TriggerKind.ROLLBACK,
            branch=None,
            commit=previous.commit,
            namespace=namespace,
            status=RunStatus.PLANNING,
            images=previous.images,
            command_plan=plan,
            started_at=self._now(),
        )
        return PlannedRelease(
            run=run,
            plan=plan,
            mode=ReleaseMode.AUTO_DEPLOY,
            namespace=namespace,
            images=previous.images,
        )

    def match_branch_rule(self, branch: str) -> BranchRule:
        for rule in self.config.branch_rules:
            if fnmatchcase(branch, rule.pattern):
                return rule
        raise PlanningError(f"no branch rule matches {branch!r}")

    def resolve_namespace(self, rule: BranchRule, branch: str) -> str | None:
        if rule.namespace:
            namespace = rule.namespace
        elif rule.namespace_template:
            slug = _safe_slug(branch.split("/", 1)[1] if "/" in branch else branch)
            namespace = rule.namespace_template.format(branch=_safe_slug(branch), slug=slug)
        else:
            namespace = None
        if namespace == "prod" and rule.mode is ReleaseMode.AUTO_DEPLOY:
            raise PlanningError("automatic branch releases cannot resolve to prod")
        return namespace

    def _branch_steps(
        self,
        branch: str,
        commit: str,
        images: ImageRefs,
        namespace: str | None,
        mode: ReleaseMode,
        run_id: str,
    ) -> list[CommandStep]:
        repo_cwd = self.config.repo.path
        steps = [
            CommandStep(
                name="git-fetch",
                argv=("git", "fetch", self.config.repo.remote, branch),
                cwd=repo_cwd,
            ),
            CommandStep(
                name="git-checkout",
                argv=("git", "checkout", "--detach", commit),
                cwd=repo_cwd,
            ),
            CommandStep(
                name="git-submodule-sync",
                argv=("git", "submodule", "sync", "--recursive"),
                cwd=repo_cwd,
            ),
        ]
        if self.config.repo.submodules:
            steps.append(
                CommandStep(
                    name="git-submodule-update",
                    argv=(
                        "git",
                        "submodule",
                        "update",
                        "--init",
                        "--recursive",
                        *self.config.repo.submodules,
                    ),
                    cwd=repo_cwd,
                )
            )
        for index, command in enumerate(self.config.deploy.verify_commands, start=1):
            steps.append(CommandStep(name=f"verify-{index}", argv=command, cwd=repo_cwd))
        steps.extend(
            [
                CommandStep(
                    name="build-api-backend",
                    argv=(
                        "docker",
                        "build",
                        "-f",
                        "docker/api-backend/Dockerfile",
                        "-t",
                        images.api_image,
                        ".",
                    ),
                    cwd=repo_cwd,
                ),
                CommandStep(
                    name="build-llm-factory",
                    argv=(
                        "docker",
                        "build",
                        "-f",
                        "docker/llm-factory/Dockerfile",
                        "-t",
                        images.factory_image,
                        "novaic-llm-factory",
                    ),
                    cwd=repo_cwd,
                ),
                CommandStep(name="push-api-backend", argv=("docker", "push", images.api_image)),
                CommandStep(name="push-llm-factory", argv=("docker", "push", images.factory_image)),
            ]
        )
        if mode is ReleaseMode.AUTO_DEPLOY:
            if namespace is None:
                raise PlanningError("auto_deploy branch plan needs a namespace")
            steps.extend(self._deploy_steps(namespace, images, run_id, commit))
        return steps

    def _deploy_steps(
        self,
        namespace: str,
        images: ImageRefs,
        run_id: str,
        commit: str,
    ) -> list[CommandStep]:
        deploy_env = self._controller_deploy_env(namespace, run_id, commit)
        steps = [
            CommandStep(
                name=f"deploy-api-{namespace}",
                argv=(self.config.deploy.script_path, "services-image", namespace, images.api_image),
                env=deploy_env,
            ),
            CommandStep(
                name=f"deploy-factory-{namespace}",
                argv=(self.config.deploy.script_path, "factory-image", namespace, images.factory_image),
                env=deploy_env,
            ),
        ]
        health_url = self.config.deploy.health_urls.get(namespace)
        if health_url:
            steps.append(
                CommandStep(
                    name=f"smoke-{namespace}",
                    argv=("curl", "-fsS", health_url),
                )
            )
        return steps

    def _controller_deploy_env(self, namespace: str, run_id: str, commit: str) -> dict[str, str]:
        return {
            "NOVAIC_DEPLOY_CALLER": "release-controller",
            "NOVAIC_RELEASE_CONTROLLER_RUN_ID": run_id,
            "NOVAIC_RELEASE_CONTROLLER_NAMESPACE": namespace,
            "NOVAIC_RELEASE_CONTROLLER_COMMIT": commit,
        }

    def _run_id(self, name: str, commit: str) -> str:
        timestamp = self.clock().strftime("%Y%m%d-%H%M%S")
        return f"{timestamp}-{_safe_slug(name)}-{commit[:12]}"

    def _now(self) -> str:
        return self.clock().isoformat()


def is_immutable_image_ref(ref: str) -> bool:
    if "@sha256:" in ref:
        digest = ref.rsplit("@sha256:", 1)[1]
        return bool(re.fullmatch(r"[0-9a-fA-F]{64}", digest))
    tag = _image_tag(ref)
    return bool(tag and _SHA_TAG_RE.fullmatch(tag) and tag not in _MUTABLE_TAGS)


def assert_immutable_image_ref(ref: str) -> None:
    if not is_immutable_image_ref(ref):
        raise PlanningError(f"image ref must be immutable sha tag or digest: {ref}")


def _image_tag(ref: str) -> str | None:
    last_segment = ref.rsplit("/", 1)[-1]
    if ":" not in last_segment:
        return None
    return last_segment.rsplit(":", 1)[1]


def _safe_slug(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    if not slug:
        raise PlanningError("cannot create namespace slug from empty value")
    return slug
