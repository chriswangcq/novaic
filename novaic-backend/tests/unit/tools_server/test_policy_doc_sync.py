"""
Sync-check: verify that key runner-OS policy tokens are consistent across
the canonical policy files and that mandatory handoff docs exist.
This test is a CI gate: if one file is updated without updating the others,
it will fail and prompt the author to keep all three in sync.

Covered files:
- scripts/tools/RUNNER_SUPPORT_POLICY.md      (primary policy document)
- tools_server/RELIABILITY_POLICY.md          (reliability policy with env dep section)
- tools_server/OPERATOR_RUNBOOK.md            (operator runbook — handoff artifact)
- scripts/tools/ci_preflight_probe_prereqs.sh (implementation; must reflect policy)
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]

RUNNER_SUPPORT_POLICY = REPO_ROOT / "scripts" / "tools" / "RUNNER_SUPPORT_POLICY.md"
RELIABILITY_POLICY = REPO_ROOT / "tools_server" / "RELIABILITY_POLICY.md"
OPERATOR_RUNBOOK = REPO_ROOT / "tools_server" / "OPERATOR_RUNBOOK.md"
CI_PREFLIGHT = REPO_ROOT / "scripts" / "tools" / "ci_preflight_probe_prereqs.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestPolicyDocSync:
    """All canonical policy/handoff files must exist and contain consistent tokens."""

    def test_runner_support_policy_exists(self) -> None:
        assert RUNNER_SUPPORT_POLICY.exists(), (
            f"Runner support policy file missing: {RUNNER_SUPPORT_POLICY}"
        )

    def test_operator_runbook_exists(self) -> None:
        """Operator runbook is a mandatory handoff artifact."""
        assert OPERATOR_RUNBOOK.exists(), (
            f"Operator runbook missing: {OPERATOR_RUNBOOK} — "
            "required for handoff and long-term operations"
        )

    def test_operator_runbook_references_leak_probe(self) -> None:
        """Runbook must reference the leak probe so operators can find it."""
        text = _read(OPERATOR_RUNBOOK)
        assert "leak_probe" in text, (
            "OPERATOR_RUNBOOK.md must reference leak_probe.sh"
        )

    def test_operator_runbook_references_reliability_policy(self) -> None:
        """Runbook must reference the full reliability policy."""
        text = _read(OPERATOR_RUNBOOK)
        assert "RELIABILITY_POLICY" in text, (
            "OPERATOR_RUNBOOK.md must reference RELIABILITY_POLICY.md"
        )

    def test_reliability_policy_has_env_dep_section(self) -> None:
        text = _read(RELIABILITY_POLICY)
        assert "Environment Dependency Policy" in text, (
            "RELIABILITY_POLICY.md must contain 'Environment Dependency Policy' section"
        )

    def test_all_three_files_mention_option_a(self) -> None:
        """Policy choice Option A must be declared in all three files."""
        for path in (RUNNER_SUPPORT_POLICY, RELIABILITY_POLICY, CI_PREFLIGHT):
            text = _read(path)
            assert "Option A" in text, (
                f"'Option A' token missing from {path.name} — policy sync required"
            )

    def test_all_three_files_mention_ubuntu(self) -> None:
        """Ubuntu support must be explicit in all three files."""
        for path in (RUNNER_SUPPORT_POLICY, RELIABILITY_POLICY, CI_PREFLIGHT):
            text = _read(path)
            assert "Ubuntu" in text or "ubuntu" in text, (
                f"'Ubuntu' token missing from {path.name} — policy sync required"
            )

    def test_all_three_files_mention_non_linux(self) -> None:
        """Non-Linux runner handling statement must appear in all three files."""
        for path in (RUNNER_SUPPORT_POLICY, RELIABILITY_POLICY, CI_PREFLIGHT):
            text = _read(path)
            assert "non-Linux" in text.lower() or "Non-Linux" in text or "non_linux" in text.lower(), (
                f"Non-Linux runner handling not documented in {path.name} — policy sync required"
            )

    def test_runner_support_policy_references_reliability_policy(self) -> None:
        """RUNNER_SUPPORT_POLICY must cross-reference RELIABILITY_POLICY.md."""
        text = _read(RUNNER_SUPPORT_POLICY)
        assert "RELIABILITY_POLICY" in text, (
            "RUNNER_SUPPORT_POLICY.md must reference RELIABILITY_POLICY.md "
            "so readers can find the full policy"
        )

    def test_runner_support_policy_references_ci_preflight(self) -> None:
        """RUNNER_SUPPORT_POLICY must cross-reference the CI preflight script."""
        text = _read(RUNNER_SUPPORT_POLICY)
        assert "ci_preflight_probe_prereqs" in text, (
            "RUNNER_SUPPORT_POLICY.md must reference ci_preflight_probe_prereqs.sh"
        )

    def test_ci_preflight_references_policy_doc(self) -> None:
        """CI preflight script must reference the policy decision document."""
        text = _read(CI_PREFLIGHT)
        assert "RUNNER_SUPPORT_POLICY" in text or "RELIABILITY_POLICY" in text, (
            "ci_preflight_probe_prereqs.sh must reference at least one policy doc "
            "so CI maintainers can find the decision record"
        )
