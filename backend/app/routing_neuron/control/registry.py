"""Canonical control registry for Codex-driven system iterations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


CONTROL_DIR_PATH = Path(__file__).resolve().parent
CODEX_CONTROL_REGISTRY_PATH = CONTROL_DIR_PATH / "codex_control_registry.json"
CODEX_CONTROL_REGISTRY_VERSION = "1.3"
CODEX_CONTROL_SCHEMA_VERSION = "codex_control_registry.v1.3"

_ENTRY_LIST_FIELDS = (
    "prompts_applied",
    "files_modified",
    "files_created",
    "files_deleted",
    "files_moved",
    "modules_touched",
    "contracts_affected",
    "tests_run",
    "smokes_run",
    "runtime_observations",
    "regressions_detected",
    "regressions_fixed",
    "aura_changes",
    "rn_changes",
    "model_bank_changes",
    "open_debts",
    "fallback_patterns",
    "degradation_patterns",
    "critic_patterns",
    "router_patterns",
    "long_tail_failures",
    "production_models",
    "candidate_models",
    "lab_models",
    "blocked_models",
    "model_family_notes",
    "promotion_candidates",
    "do_not_promote_notes",
    "rn_recent_outcomes",
    "rn_recommendations",
    "rn_attention_points",
    "rn_memory_notes",
    "review_artifacts_needed",
)


@dataclass(frozen=True)
class CodexControlStatus:
    registry_path: str
    registry_version: str
    schema_version: str
    entry_count: int
    latest_run_id: str | None
    latest_timestamp: str | None
    latest_version: str | None
    latest_status: str | None
    latest_work_type: str | None
    latest_requested_scope: str | None
    latest_summary: str | None
    latest_checkpoint: str | None
    latest_checkpoint_short: str | None
    latest_checkpoint_long: str | None
    latest_tests_status: str | None
    latest_smokes_status: str | None
    latest_runtime_health: str | None
    latest_test_health: str | None
    latest_risk: str | None
    latest_next_step: str | None
    latest_open_debts: tuple[str, ...]
    latest_files_modified_count: int
    latest_files_created_count: int
    latest_modules_touched: tuple[str, ...]
    latest_contracts_affected: tuple[str, ...]
    latest_known_good: str | None
    latest_known_weakness: str | None
    latest_version_closed_for_scope: str | None
    latest_review_artifacts_needed: tuple[str, ...]
    latest_fallback_patterns: tuple[str, ...]
    latest_degradation_patterns: tuple[str, ...]
    latest_critic_patterns: tuple[str, ...]
    latest_router_patterns: tuple[str, ...]
    latest_long_tail_failures: tuple[str, ...]
    latest_rn_recent_outcomes: tuple[str, ...]
    latest_rn_recommendations: tuple[str, ...]
    latest_rn_attention_points: tuple[str, ...]
    latest_production_models: tuple[str, ...]
    latest_candidate_models: tuple[str, ...]
    latest_lab_models: tuple[str, ...]
    latest_do_not_promote_notes: tuple[str, ...]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _normalize_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return [
            item
            for item in (_normalize_string(entry) for entry in value)
            if item
        ]

    normalized = _normalize_string(value)
    return [normalized] if normalized else []


def _normalize_result_block(value: Any, *, default_status: str) -> dict[str, Any]:
    if isinstance(value, dict):
        status = _normalize_string(value.get("status"), default_status)
        details = _normalize_string_list(value.get("details"))
        summary = _normalize_string(value.get("summary"))
        return {
            "status": status,
            "summary": summary,
            "details": details,
        }

    normalized = _normalize_string(value, default_status)
    return {
        "status": normalized or default_status,
        "summary": "",
        "details": [],
    }


def _build_empty_entry() -> dict[str, Any]:
    entry = {
        "run_id": "",
        "timestamp": "",
        "version_target": "",
        "work_type": "",
        "work_scope": "",
        "requested_scope": "",
        "summary": "",
        "checkpoint_short": "",
        "checkpoint_long": "",
        "status": "pending",
        "next_recommended_step": "",
        "smoke_consistency": "",
        "runtime_quality_observed": "",
        "model_failures_observed": "",
        "benchmark_readiness": "",
        "rn_operational_state": "",
        "rn_signal_state": "",
        "rn_memory_notes_summary": "",
        "handoff": "",
        "review_minimal": "",
        "known_good": "",
        "known_weakness": "",
        "version_closed_for_scope": "",
        "tests_passed_count": 0,
        "tests_failed_count": 0,
        "rn_applied_count": 0,
        "rn_blocked_count": 0,
        "rn_no_signal_count": 0,
        "tests_result": _normalize_result_block(None, default_status="not_run"),
        "smokes_result": _normalize_result_block(None, default_status="not_run"),
    }
    for field_name in _ENTRY_LIST_FIELDS:
        entry[field_name] = []
    return entry


def _derive_smoke_consistency(entry: dict[str, Any]) -> str:
    explicit = _normalize_string(entry.get("smoke_consistency"))
    if explicit:
        return explicit

    smokes_status = _normalize_string(entry["smokes_result"]["status"], "not_run")
    if smokes_status == "ok":
        return "consistent"
    if smokes_status in {"mixed", "degraded"}:
        return "mixed"
    if smokes_status in {"failed", "error"}:
        return "unstable"
    return "not_run"


def _derive_runtime_health(entry: dict[str, Any]) -> str:
    if not entry:
        return "empty"

    status = _normalize_string(entry.get("status"), "pending")
    tests_status = _normalize_string(entry["tests_result"]["status"], "not_run")
    smokes_status = _normalize_string(entry["smokes_result"]["status"], "not_run")
    regressions = list(entry.get("regressions_detected", []))
    long_tail_failures = list(entry.get("long_tail_failures", []))
    model_failures = _normalize_string(entry.get("model_failures_observed"))

    if status not in {"completed", "closed_for_scope"}:
        return "in_progress"
    if tests_status in {"failed", "error"} or regressions:
        return "degraded"
    if smokes_status in {"mixed", "degraded"} or long_tail_failures or model_failures:
        return "watch"
    if smokes_status in {"failed", "error"}:
        return "unstable"
    return "healthy"


def _derive_test_health(entry: dict[str, Any]) -> str:
    if not entry:
        return "not_run"

    tests_status = _normalize_string(entry["tests_result"]["status"], "not_run")
    failed_count = _normalize_int(entry.get("tests_failed_count"))
    if tests_status in {"failed", "error"} or failed_count > 0:
        return "failing"
    if tests_status == "ok":
        return "healthy"
    return tests_status


def _derive_risk(entry: dict[str, Any]) -> str:
    if not entry:
        return "unknown"

    if _derive_test_health(entry) == "failing":
        return "high"
    if entry.get("regressions_detected"):
        return "high"

    smokes_status = _normalize_string(entry["smokes_result"]["status"], "not_run")
    if smokes_status in {"failed", "error"}:
        return "high"
    if smokes_status in {"mixed", "degraded"}:
        return "medium"

    if (
        entry.get("open_debts")
        or entry.get("long_tail_failures")
        or _normalize_string(entry.get("model_failures_observed"))
    ):
        return "medium"

    return "low"


def normalize_codex_control_entry(value: dict[str, Any] | None) -> dict[str, Any]:
    raw = value or {}
    entry = _build_empty_entry()

    entry["run_id"] = _normalize_string(raw.get("run_id"))
    entry["timestamp"] = _normalize_string(raw.get("timestamp"), _utc_now_iso())
    entry["version_target"] = _normalize_string(raw.get("version_target"))
    entry["work_type"] = _normalize_string(raw.get("work_type"))
    entry["work_scope"] = _normalize_string(
        raw.get("work_scope"),
        _normalize_string(raw.get("requested_scope")),
    )
    entry["requested_scope"] = _normalize_string(
        raw.get("requested_scope"),
        entry["work_scope"],
    )
    entry["summary"] = _normalize_string(raw.get("summary"))
    entry["checkpoint_short"] = _normalize_string(raw.get("checkpoint_short"))
    entry["checkpoint_long"] = _normalize_string(
        raw.get("checkpoint_long"),
        entry["checkpoint_short"],
    )
    entry["status"] = _normalize_string(raw.get("status"), "pending")
    entry["next_recommended_step"] = _normalize_string(raw.get("next_recommended_step"))
    entry["smoke_consistency"] = _normalize_string(raw.get("smoke_consistency"))
    entry["runtime_quality_observed"] = _normalize_string(
        raw.get("runtime_quality_observed"),
    )
    entry["model_failures_observed"] = _normalize_string(
        raw.get("model_failures_observed"),
    )
    entry["benchmark_readiness"] = _normalize_string(raw.get("benchmark_readiness"))
    entry["rn_operational_state"] = _normalize_string(raw.get("rn_operational_state"))
    entry["rn_signal_state"] = _normalize_string(raw.get("rn_signal_state"))
    entry["rn_memory_notes_summary"] = _normalize_string(
        raw.get("rn_memory_notes_summary"),
    )
    entry["handoff"] = _normalize_string(raw.get("handoff"))
    entry["review_minimal"] = _normalize_string(raw.get("review_minimal"))
    entry["known_good"] = _normalize_string(raw.get("known_good"))
    entry["known_weakness"] = _normalize_string(raw.get("known_weakness"))
    entry["version_closed_for_scope"] = _normalize_string(
        raw.get("version_closed_for_scope"),
        entry["version_target"] if entry["status"] in {"completed", "closed_for_scope"} else "",
    )

    for field_name in _ENTRY_LIST_FIELDS:
        entry[field_name] = _normalize_string_list(raw.get(field_name))

    entry["tests_result"] = _normalize_result_block(
        raw.get("tests_result"),
        default_status="not_run",
    )
    entry["smokes_result"] = _normalize_result_block(
        raw.get("smokes_result"),
        default_status="not_run",
    )
    entry["tests_passed_count"] = _normalize_int(raw.get("tests_passed_count"))
    entry["tests_failed_count"] = _normalize_int(raw.get("tests_failed_count"))
    entry["rn_applied_count"] = _normalize_int(raw.get("rn_applied_count"))
    entry["rn_blocked_count"] = _normalize_int(raw.get("rn_blocked_count"))
    entry["rn_no_signal_count"] = _normalize_int(raw.get("rn_no_signal_count"))

    if not entry["run_id"]:
        timestamp_token = entry["timestamp"].replace(":", "").replace("-", "")
        entry["run_id"] = f"codex-{timestamp_token[:15] or 'run'}"

    if not entry["checkpoint_short"]:
        entry["checkpoint_short"] = entry["summary"]
    if not entry["checkpoint_long"]:
        entry["checkpoint_long"] = entry["checkpoint_short"] or entry["summary"]
    if not entry["review_minimal"]:
        entry["review_minimal"] = entry["checkpoint_short"] or entry["summary"]
    if not entry["known_good"] and entry["smokes_result"]["status"] == "ok":
        entry["known_good"] = entry["smokes_result"]["summary"] or "smokes estables"
    if not entry["known_weakness"] and entry["open_debts"]:
        entry["known_weakness"] = entry["open_debts"][0]
    if not entry["rn_memory_notes_summary"] and entry["rn_memory_notes"]:
        entry["rn_memory_notes_summary"] = entry["rn_memory_notes"][0]
    if not entry["handoff"]:
        entry["handoff"] = entry["next_recommended_step"] or entry["checkpoint_short"]
    if not entry["smoke_consistency"]:
        entry["smoke_consistency"] = _derive_smoke_consistency(entry)

    return entry


def _build_latest_block(entry: dict[str, Any] | None) -> dict[str, Any]:
    if entry is None:
        return {
            "run_id": None,
            "timestamp": None,
            "version_target": None,
            "status": "empty",
            "work_type": None,
            "requested_scope": None,
            "summary": None,
            "checkpoint_short": None,
            "checkpoint_long": None,
            "tests_status": "not_run",
            "smokes_status": "not_run",
            "runtime_health": "empty",
            "test_health": "not_run",
            "risk": "unknown",
            "next_recommended_step": None,
            "open_debts": [],
            "files_modified_count": 0,
            "files_created_count": 0,
            "modules_touched": [],
            "contracts_affected": [],
            "known_good": None,
            "known_weakness": None,
            "version_closed_for_scope": None,
            "review_artifacts_needed": [],
        }

    return {
        "run_id": entry["run_id"],
        "timestamp": entry["timestamp"],
        "version_target": entry["version_target"],
        "status": entry["status"],
        "work_type": entry["work_type"],
        "requested_scope": entry["requested_scope"],
        "summary": entry["summary"],
        "checkpoint_short": entry["checkpoint_short"],
        "checkpoint_long": entry["checkpoint_long"],
        "tests_status": entry["tests_result"]["status"],
        "smokes_status": entry["smokes_result"]["status"],
        "runtime_health": _derive_runtime_health(entry),
        "test_health": _derive_test_health(entry),
        "risk": _derive_risk(entry),
        "next_recommended_step": entry["next_recommended_step"],
        "open_debts": list(entry["open_debts"]),
        "files_modified_count": len(entry["files_modified"]),
        "files_created_count": len(entry["files_created"]),
        "modules_touched": list(entry["modules_touched"]),
        "contracts_affected": list(entry["contracts_affected"]),
        "known_good": entry["known_good"],
        "known_weakness": entry["known_weakness"],
        "version_closed_for_scope": entry["version_closed_for_scope"] or None,
        "review_artifacts_needed": list(entry["review_artifacts_needed"]),
    }


def _build_registry_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    completed_entries = sum(
        1
        for entry in entries
        if entry["status"] in {"completed", "closed_for_scope"}
    )
    in_progress_entries = sum(1 for entry in entries if entry["status"] == "in_progress")
    versions = [
        entry["version_target"]
        for entry in entries
        if entry["version_target"]
    ]
    return {
        "total_entries": len(entries),
        "completed_entries": completed_entries,
        "in_progress_entries": in_progress_entries,
        "closed_versions": versions,
    }


def _build_known_issues(entries: list[dict[str, Any]]) -> dict[str, Any]:
    latest_entry = entries[-1] if entries else None
    latest_open_debts = list(latest_entry["open_debts"]) if latest_entry is not None else []
    latest_regressions = list(latest_entry["regressions_detected"]) if latest_entry is not None else []
    latest_long_tail = list(latest_entry["long_tail_failures"]) if latest_entry is not None else []
    return {
        "latest_open_debts": latest_open_debts,
        "latest_regressions_detected": latest_regressions,
        "latest_long_tail_failures": latest_long_tail,
    }


def _build_runtime_patterns(entries: list[dict[str, Any]]) -> dict[str, Any]:
    latest_entry = entries[-1] if entries else None
    if latest_entry is None:
        return {
            "fallback_patterns": [],
            "degradation_patterns": [],
            "critic_patterns": [],
            "router_patterns": [],
        }
    return {
        "fallback_patterns": list(latest_entry["fallback_patterns"]),
        "degradation_patterns": list(latest_entry["degradation_patterns"]),
        "critic_patterns": list(latest_entry["critic_patterns"]),
        "router_patterns": list(latest_entry["router_patterns"]),
    }


def _build_model_bank_snapshot(entries: list[dict[str, Any]]) -> dict[str, Any]:
    latest_entry = entries[-1] if entries else None
    if latest_entry is None:
        return {
            "production_models": [],
            "candidate_models": [],
            "lab_models": [],
            "benchmark_readiness": "",
            "blocked_models": [],
            "promotion_candidates": [],
            "do_not_promote_notes": [],
            "model_family_notes": [],
        }
    return {
        "production_models": list(latest_entry["production_models"]),
        "candidate_models": list(latest_entry["candidate_models"]),
        "lab_models": list(latest_entry["lab_models"]),
        "benchmark_readiness": latest_entry["benchmark_readiness"],
        "blocked_models": list(latest_entry["blocked_models"]),
        "promotion_candidates": list(latest_entry["promotion_candidates"]),
        "do_not_promote_notes": list(latest_entry["do_not_promote_notes"]),
        "model_family_notes": list(latest_entry["model_family_notes"]),
    }


def _build_latest_review_block(entry: dict[str, Any] | None) -> dict[str, Any]:
    if entry is None:
        return {
            "handoff": None,
            "minimal": None,
            "known_good": None,
            "known_weakness": None,
            "artifacts_needed": [],
        }
    return {
        "handoff": entry["handoff"] or entry["next_recommended_step"] or entry["checkpoint_short"],
        "minimal": entry["review_minimal"] or entry["checkpoint_short"] or entry["summary"],
        "known_good": entry["known_good"],
        "known_weakness": entry["known_weakness"],
        "artifacts_needed": list(entry["review_artifacts_needed"]),
    }


def build_empty_codex_control_registry() -> dict[str, Any]:
    return {
        "registry_version": CODEX_CONTROL_REGISTRY_VERSION,
        "schema_version": CODEX_CONTROL_SCHEMA_VERSION,
        "latest_version": None,
        "latest_status": "empty",
        "latest_checkpoint": None,
        "latest_checkpoint_short": None,
        "latest_runtime_health": "empty",
        "latest_test_health": "not_run",
        "latest_risk": "unknown",
        "latest_open_debts": [],
        "latest_next_step": None,
        "latest_version_closed_for_scope": None,
        "latest_handoff": None,
        "latest_review_minimal": None,
        "latest_known_good": None,
        "latest_known_weakness": None,
        "latest_review_artifacts_needed": [],
        "latest": _build_latest_block(None),
        "stats": _build_registry_stats([]),
        "known_issues": _build_known_issues([]),
        "runtime_patterns": _build_runtime_patterns([]),
        "model_bank": _build_model_bank_snapshot([]),
        "entries": [],
    }


def _registry_path(path: str | Path | None = None) -> Path:
    return Path(path).expanduser().resolve(strict=False) if path is not None else CODEX_CONTROL_REGISTRY_PATH


def ensure_codex_control_registry(path: str | Path | None = None) -> Path:
    registry_path = _registry_path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if not registry_path.exists():
        normalized = normalize_codex_control_registry(build_empty_codex_control_registry())
        registry_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return registry_path


def normalize_codex_control_registry(value: dict[str, Any] | None) -> dict[str, Any]:
    raw = value or {}
    entries = [
        normalize_codex_control_entry(entry)
        for entry in raw.get("entries", [])
        if isinstance(entry, dict)
    ]
    latest_entry = entries[-1] if entries else None
    latest = _build_latest_block(latest_entry)
    latest_review = _build_latest_review_block(latest_entry)

    return {
        "registry_version": _normalize_string(
            raw.get("registry_version"),
            CODEX_CONTROL_REGISTRY_VERSION,
        ),
        "schema_version": _normalize_string(
            raw.get("schema_version"),
            CODEX_CONTROL_SCHEMA_VERSION,
        ),
        "latest_version": latest["version_target"],
        "latest_status": latest["status"],
        "latest_checkpoint": latest["checkpoint_long"],
        "latest_checkpoint_short": latest["checkpoint_short"],
        "latest_runtime_health": latest["runtime_health"],
        "latest_test_health": latest["test_health"],
        "latest_risk": latest["risk"],
        "latest_open_debts": list(latest["open_debts"]),
        "latest_next_step": latest["next_recommended_step"],
        "latest_version_closed_for_scope": latest["version_closed_for_scope"],
        "latest_handoff": latest_review["handoff"],
        "latest_review_minimal": latest_review["minimal"],
        "latest_known_good": latest_review["known_good"],
        "latest_known_weakness": latest_review["known_weakness"],
        "latest_review_artifacts_needed": list(latest_review["artifacts_needed"]),
        "latest": latest,
        "stats": _build_registry_stats(entries),
        "known_issues": _build_known_issues(entries),
        "runtime_patterns": _build_runtime_patterns(entries),
        "model_bank": _build_model_bank_snapshot(entries),
        "entries": entries,
    }


def load_codex_control_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = ensure_codex_control_registry(path)
    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = build_empty_codex_control_registry()
        save_codex_control_registry(raw, path=registry_path)
        return raw

    normalized = normalize_codex_control_registry(raw)
    if normalized != raw:
        save_codex_control_registry(normalized, path=registry_path)
    return normalized


def save_codex_control_registry(
    registry: dict[str, Any],
    *,
    path: str | Path | None = None,
) -> Path:
    registry_path = _registry_path(path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_codex_control_registry(registry)
    registry_path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return registry_path


def update_codex_control_registry(
    entry: dict[str, Any],
    *,
    path: str | Path | None = None,
) -> dict[str, Any]:
    registry = load_codex_control_registry(path)
    normalized_entry = normalize_codex_control_entry(entry)
    entries = list(registry["entries"])

    for index, existing_entry in enumerate(entries):
        if existing_entry["run_id"] == normalized_entry["run_id"]:
            entries[index] = normalized_entry
            break
    else:
        entries.append(normalized_entry)

    updated = normalize_codex_control_registry(
        {
            "registry_version": registry["registry_version"],
            "schema_version": registry["schema_version"],
            "entries": entries,
        }
    )
    save_codex_control_registry(updated, path=path)
    return updated


def build_codex_control_status(path: str | Path | None = None) -> CodexControlStatus:
    registry = load_codex_control_registry(path)
    latest = registry["latest"]
    latest_entry = registry["entries"][-1] if registry["entries"] else None
    runtime_patterns = registry.get("runtime_patterns", {})
    model_bank = registry.get("model_bank", {})

    return CodexControlStatus(
        registry_path=str(_registry_path(path)),
        registry_version=registry["registry_version"],
        schema_version=registry["schema_version"],
        entry_count=len(registry["entries"]),
        latest_run_id=latest["run_id"],
        latest_timestamp=latest["timestamp"],
        latest_version=latest["version_target"],
        latest_status=latest["status"],
        latest_work_type=latest["work_type"],
        latest_requested_scope=latest["requested_scope"],
        latest_summary=latest["summary"],
        latest_checkpoint=registry["latest_checkpoint"],
        latest_checkpoint_short=registry["latest_checkpoint_short"],
        latest_checkpoint_long=registry["latest_checkpoint"],
        latest_tests_status=latest["tests_status"],
        latest_smokes_status=latest["smokes_status"],
        latest_runtime_health=registry["latest_runtime_health"],
        latest_test_health=registry["latest_test_health"],
        latest_risk=registry["latest_risk"],
        latest_next_step=registry["latest_next_step"],
        latest_open_debts=tuple(registry["latest_open_debts"]),
        latest_files_modified_count=int(latest["files_modified_count"]),
        latest_files_created_count=int(latest["files_created_count"]),
        latest_modules_touched=tuple(latest["modules_touched"]),
        latest_contracts_affected=tuple(latest["contracts_affected"]),
        latest_known_good=registry["latest_known_good"],
        latest_known_weakness=registry["latest_known_weakness"],
        latest_version_closed_for_scope=registry["latest_version_closed_for_scope"],
        latest_review_artifacts_needed=tuple(registry["latest_review_artifacts_needed"]),
        latest_fallback_patterns=tuple(runtime_patterns.get("fallback_patterns", ())),
        latest_degradation_patterns=tuple(runtime_patterns.get("degradation_patterns", ())),
        latest_critic_patterns=tuple(runtime_patterns.get("critic_patterns", ())),
        latest_router_patterns=tuple(runtime_patterns.get("router_patterns", ())),
        latest_long_tail_failures=tuple(registry.get("known_issues", {}).get("latest_long_tail_failures", ())),
        latest_rn_recent_outcomes=tuple((latest_entry or {}).get("rn_recent_outcomes", ())),
        latest_rn_recommendations=tuple((latest_entry or {}).get("rn_recommendations", ())),
        latest_rn_attention_points=tuple((latest_entry or {}).get("rn_attention_points", ())),
        latest_production_models=tuple(model_bank.get("production_models", ())),
        latest_candidate_models=tuple(model_bank.get("candidate_models", ())),
        latest_lab_models=tuple(model_bank.get("lab_models", ())),
        latest_do_not_promote_notes=tuple(model_bank.get("do_not_promote_notes", ())),
    )


def summarize_codex_control_status(path: str | Path | None = None) -> str:
    status = build_codex_control_status(path)
    if status.entry_count == 0 or status.latest_run_id is None:
        return "registro Codex vacio, sin iteraciones consolidadas todavia"

    tests_status = status.latest_tests_status or "not_run"
    smokes_status = status.latest_smokes_status or "not_run"
    runtime_health = status.latest_runtime_health or "unknown"
    risk = status.latest_risk or "unknown"
    summary = status.latest_summary or "sin resumen breve"
    return (
        f"registro Codex activo con {status.entry_count} iteraciones; "
        f"ultimo run {status.latest_run_id} para V{status.latest_version or 'sin version'} "
        f"({status.latest_status or 'sin estado'}), tests {tests_status}, smokes {smokes_status}, "
        f"runtime {runtime_health}, riesgo {risk}; {summary}"
    )


def summarize_codex_latest_checkpoint(path: str | Path | None = None) -> str:
    status = build_codex_control_status(path)
    if status.entry_count == 0 or status.latest_run_id is None:
        return "sin checkpoint reciente de Codex"

    checkpoint = (
        status.latest_checkpoint_short
        or status.latest_summary
        or "sin checkpoint breve"
    )
    return (
        f"ultimo trabajo de Codex: V{status.latest_version or 'sin version'} "
        f"({status.latest_status or 'sin estado'}), {checkpoint}"
    )


__all__ = [
    "CODEX_CONTROL_REGISTRY_PATH",
    "CODEX_CONTROL_REGISTRY_VERSION",
    "CODEX_CONTROL_SCHEMA_VERSION",
    "CodexControlStatus",
    "build_codex_control_status",
    "build_empty_codex_control_registry",
    "ensure_codex_control_registry",
    "load_codex_control_registry",
    "normalize_codex_control_entry",
    "normalize_codex_control_registry",
    "save_codex_control_registry",
    "summarize_codex_control_status",
    "summarize_codex_latest_checkpoint",
    "update_codex_control_registry",
]
