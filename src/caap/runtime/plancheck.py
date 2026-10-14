"""Validate the complete future-work document graph without executing its tasks."""

import argparse
from fnmatch import fnmatch
from itertools import combinations
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


TASK_IDS = tuple(f"F{index:02d}" for index in range(1, 46))
REVIEWER_IDS = tuple([f"R1-{index}" for index in range(1, 8)] +
                     [f"R2-{index}" for index in range(1, 6)] +
                     [f"R3-{index}" for index in range(1, 5)])
HYPOTHESIS_IDS = tuple(f"H{index}" for index in range(1, 6))
TOP_FIELDS = {"schema_version", "plan_version", "tasks", "reviewer_ids", "hypothesis_ids"}
STRING_FIELDS = {"id", "title", "spec", "status", "cost_class"}
LIST_FIELDS = {"depends_on", "owned_paths", "inputs", "outputs", "acceptance", "evidence_for", "capabilities"}
TASK_FIELDS = STRING_FIELDS | LIST_FIELDS | {"phase"}
GLOB_TOKEN = re.compile(r"[*?\[]")
NOTICE = "Document graph validation only: planned tasks are not implemented experiments, and graph waves are not scheduling authorization."


def _result():
    return {"valid": False, "errors": [], "task_count": 0, "topological_waves": [],
            "coverage": {"reviewers": {key: [] for key in REVIEWER_IDS},
                         "hypotheses": {key: [] for key in HYPOTHESIS_IDS}, "uncovered": []},
            "possible_write_conflicts": [],
            "conflict_analysis": "conservative owned_paths literal-prefix/glob approximation; no proof of conflict-free execution",
            "document_graph_only": True, "experiments_implemented": False, "notice": NOTICE}


def _error(result, code, location, message):
    result["errors"].append({"code": code, "location": location, "message": message})


def _fields(value, expected, location, result):
    for field in sorted(expected - value.keys()):
        _error(result, "missing_field", f"{location}.{field}", "Required field is missing.")
    for field in sorted(value.keys() - expected, key=str):
        _error(result, "unknown_field", f"{location}.{field}", "Unknown field is not allowed.")


def _string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _list_field(value, location, result, nonempty=False):
    if not isinstance(value, list):
        _error(result, "invalid_type", location, "Expected a list of strings.")
        return False
    good = True
    if nonempty and not value:
        _error(result, "empty_field", location, "At least one value is required.")
        good = False
    for index, item in enumerate(value):
        if not isinstance(item, str):
            _error(result, "invalid_type", f"{location}[{index}]", "Expected a string.")
            good = False
        elif not item.strip():
            _error(result, "empty_field", f"{location}[{index}]", "Blank strings are not allowed.")
            good = False
    return good


def _check_glob_components(root, parts):
    """Inspect matching existing components without following links or reparse points."""
    pending = [(root, 0)]
    visited = set()
    work = 0
    while pending:
        current, index = pending.pop()
        if (current, index) in visited:
            continue
        visited.add((current, index))
        work += 1
        # 仅做有界静态审计；超限须缩小 owned_paths，不能把未检查路径判为安全。
        if work > 10000:
            raise ValueError("Glob path safety unverified: inspection limit exceeded; narrow the pattern.")
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError("Glob path safety unverified: matched symbolic link or reparse point is not followed.")
        if index == len(parts) or not stat.S_ISDIR(info.st_mode):
            continue
        component = parts[index]
        if not GLOB_TOKEN.search(component):
            pending.append((current / component, index + 1))
            continue
        if component == "**":
            pending.append((current, index + 1))
        with os.scandir(current) as entries:
            for entry in entries:
                work += 1
                if work > 10000:
                    raise ValueError("Glob path safety unverified: inspection limit exceeded; narrow the pattern.")
                if component == "**" or fnmatch(entry.name, component):
                    pending.append((current / entry.name, index if component == "**" else index + 1))


def _repo_path(value, root, allow_glob=False):
    """Validate syntax, existing prefixes, and bounded no-follow glob components."""
    if not value or value != value.strip() or any(ord(char) < 32 for char in value):
        raise ValueError("Path is blank, padded, or contains control characters.")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or ":" in value or ".." in path.parts or value.startswith("~") or str(path) == ".":
        raise ValueError("Expected a repository-relative path without traversal.")
    glob = GLOB_TOKEN.search(value)
    if glob and not allow_glob:
        raise ValueError("Document paths cannot contain glob tokens.")
    if glob:
        _check_glob_components(root, path.parts)
    prefix = value[:glob.start()] if glob else value
    resolved = (root / prefix).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("Path or its existing symlink prefix escapes the repository.")
    return resolved


def _task(task, location, root, result):
    if not isinstance(task, dict):
        _error(result, "invalid_type", location, "Expected a task object.")
        return
    _fields(task, TASK_FIELDS, location, result)
    for field in sorted(STRING_FIELDS & task.keys()):
        if not isinstance(task[field], str):
            _error(result, "invalid_type", f"{location}.{field}", "Expected a string.")
        elif not task[field].strip():
            _error(result, "empty_field", f"{location}.{field}", "A nonblank string is required.")
    for field in sorted(LIST_FIELDS & task.keys()):
        _list_field(task[field], f"{location}.{field}", result,
                    nonempty=field in {"owned_paths", "outputs", "acceptance"})
    if "phase" in task:
        if type(task["phase"]) is not int:
            _error(result, "invalid_type", f"{location}.phase", "Expected an integer, not a boolean.")
        elif task["phase"] < 0:
            _error(result, "invalid_phase", f"{location}.phase", "Phase must be nonnegative.")
    if isinstance(task.get("id"), str) and task["id"] not in TASK_IDS:
        _error(result, "invalid_task_id", f"{location}.id", "Task ID must be F01 through F45.")
    for field, allowed in (("status", {"planned"}), ("cost_class", {"cpu", "gpu", "human", "mixed"})):
        if isinstance(task.get(field), str) and task[field] not in allowed:
            _error(result, "invalid_value", f"{location}.{field}", f"Expected one of {sorted(allowed)}.")
    for field in ("owned_paths", "outputs", "spec"):
        if field == "spec":
            paths = [task[field]] if isinstance(task.get(field), str) and task[field].strip() else []
        else:
            paths = task.get(field) if _string_list(task.get(field)) else []
        for index, value in enumerate(paths):
            where = f"{location}.{field}" + (f"[{index}]" if field != "spec" else "")
            try:
                resolved = _repo_path(value, root, allow_glob=field != "spec")
                if field == "spec" and (resolved.suffix.lower() != ".md" or not resolved.is_file()):
                    _error(result, "invalid_spec", where, "Spec must be an existing Markdown file in the repository.")
            except (ValueError, OSError, RuntimeError) as exc:
                _error(result, "unsafe_path", where, str(exc))


def paths_may_overlap(left, right):
    """Overapproximate overlap: a negative result is not a filesystem safety proof."""
    left, right = str(PurePosixPath(left)), str(PurePosixPath(right))
    left_glob, right_glob = GLOB_TOKEN.search(left), GLOB_TOKEN.search(right)
    if not left_glob and not right_glob:
        return left == right or left.startswith(right.rstrip("/") + "/") or right.startswith(left.rstrip("/") + "/")
    left_prefix = left[:left_glob.start()] if left_glob else left
    right_prefix = right[:right_glob.start()] if right_glob else right
    return left_prefix.startswith(right_prefix) or right_prefix.startswith(left_prefix)


def _graph(nodes, result):
    dependencies = {task_id: set() for task_id in nodes}
    for task_id, task in nodes.items():
        refs = task.get("depends_on")
        if not _string_list(refs):
            continue
        if len(refs) != len(set(refs)):
            _error(result, "duplicate_dependency", f"{task_id}.depends_on", "Dependencies must be unique.")
        for parent in sorted(set(refs)):
            if parent not in nodes:
                _error(result, "unknown_dependency", f"{task_id}.depends_on", f"Dependency {parent!r} has no valid task.")
                continue
            dependencies[task_id].add(parent)
            if parent == task_id:
                _error(result, "self_dependency", f"{task_id}.depends_on", "Task cannot depend on itself.")
            phase, parent_phase = task.get("phase"), nodes[parent].get("phase")
            if type(phase) is int and type(parent_phase) is int and parent_phase > phase:
                _error(result, "phase_order", f"{task_id}.depends_on", f"Dependency {parent} is in a later phase.")
    pending = {key: value.copy() for key, value in dependencies.items()}
    while pending:
        wave = sorted(key for key, parents in pending.items() if not parents)
        if not wave:
            _error(result, "dependency_cycle", "tasks", "Cycle or cycle-blocked tasks: " + ", ".join(sorted(pending)))
            break
        result["topological_waves"].append(wave)
        for key in wave:
            del pending[key]
        for parents in pending.values():
            parents.difference_update(wave)
    return dependencies


def _conflicts(nodes, dependencies, result):
    ancestors = {}
    for task_id in nodes:
        seen = set()
        pending = list(dependencies[task_id])
        while pending:
            parent = pending.pop()
            if parent not in seen:
                seen.add(parent)
                pending.extend(dependencies[parent] - seen)
        ancestors[task_id] = seen
    for left, right in combinations(sorted(nodes), 2):
        left_paths, right_paths = nodes[left].get("owned_paths"), nodes[right].get("owned_paths")
        if not _string_list(left_paths) or not _string_list(right_paths):
            continue
        overlap = [[a, b] for a in left_paths for b in right_paths if paths_may_overlap(a, b)]
        if overlap:
            result["possible_write_conflicts"].append({"task_ids": [left, right], "path_pairs": overlap,
                                                       "dependency_ordered": left in ancestors[right] or right in ancestors[left]})


def validate_manifest(manifest, repo_root):
    result = _result()
    try:
        root = Path(repo_root).resolve()
        if not root.is_dir():
            raise ValueError("Repository root is not an existing directory.")
    except (OSError, ValueError, RuntimeError) as exc:
        _error(result, "invalid_repo_root", "repo_root", str(exc))
        return result
    if not isinstance(manifest, dict):
        _error(result, "invalid_type", "$", "Manifest must be an object.")
        return result
    _fields(manifest, TOP_FIELDS, "$", result)
    for field, expected in (("schema_version", "caap.tasks.v2"), ("plan_version", "caap-full-v2")):
        if field in manifest:
            if not isinstance(manifest[field], str):
                _error(result, "invalid_type", field, "Expected a string.")
            elif manifest[field] != expected:
                _error(result, "invalid_version", field, f"Expected {expected!r}.")
    for field, expected in (("reviewer_ids", REVIEWER_IDS), ("hypothesis_ids", HYPOTHESIS_IDS)):
        if field in manifest and _list_field(manifest[field], field, result):
            if len(manifest[field]) != len(expected) or set(manifest[field]) != set(expected):
                _error(result, "invalid_registry", field, "Registry must contain exactly the canonical IDs, each once.")
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        _error(result, "invalid_type", "tasks", "Expected a list of task objects.")
        return result
    result["task_count"] = len(tasks)
    nodes = {}
    for index, task in enumerate(tasks):
        _task(task, f"tasks[{index}]", root, result)
        task_id = task.get("id") if isinstance(task, dict) else None
        if not isinstance(task_id, str) or task_id not in TASK_IDS:
            continue
        if task_id in nodes:
            _error(result, "duplicate_task_id", f"tasks[{index}].id", f"Duplicate task ID {task_id}.")
        else:
            nodes[task_id] = task
    missing = sorted(set(TASK_IDS) - nodes.keys())
    if missing:
        _error(result, "missing_task_ids", "tasks", "Missing required tasks: " + ", ".join(missing))
    coverage = dict(result["coverage"]["reviewers"], **result["coverage"]["hypotheses"])
    for task_id, task in nodes.items():
        evidence = task.get("evidence_for")
        if not _string_list(evidence):
            continue
        for item in sorted(set(evidence)):
            if item not in coverage:
                _error(result, "unknown_evidence_id", f"{task_id}.evidence_for", f"Unknown reviewer/hypothesis ID {item!r}.")
            else:
                coverage[item].append(task_id)
    uncovered = [key for key, owners in coverage.items() if not owners]
    result["coverage"]["uncovered"] = uncovered
    if uncovered:
        _error(result, "missing_evidence_coverage", "tasks.evidence_for", "No task covers: " + ", ".join(uncovered))
    dependencies = _graph(nodes, result)
    _conflicts(nodes, dependencies, result)
    result["valid"] = not result["errors"]
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"Nonstandard JSON constant: {value}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=NOTICE)
    parser.add_argument("--manifest", default="plan/tasks.json", help="manifest path (relative to repository root by default)")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="repository root (default current directory)")
    args = parser.parse_args(argv)
    result = _result()
    try:
        root = args.repo_root.resolve()
        if not root.is_dir():
            raise ValueError("Repository root is not an existing directory.")
        manifest_path = Path(args.manifest)
        if manifest_path.is_absolute():
            manifest_path = manifest_path.resolve()
            if root not in manifest_path.parents:
                raise ValueError("Manifest escapes the repository root.")
        else:
            manifest_path = _repo_path(args.manifest, root)
    except (OSError, ValueError, RuntimeError) as exc:
        _error(result, "unsafe_path", "manifest", str(exc))
    else:
        try:
            with manifest_path.open(encoding="utf-8") as handle:
                manifest = json.load(handle, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        except OSError as exc:
            _error(result, "manifest_read_error", "manifest", str(exc))
        except (ValueError, UnicodeError, RecursionError) as exc:
            _error(result, "manifest_parse_error", "manifest", str(exc))
        else:
            result = validate_manifest(manifest, root)
    print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
