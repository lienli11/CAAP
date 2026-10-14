"""旧物理记录诊断，不是 v2 物理协议或论文证据。

CSV 列: subject, attempt, success, condition, model。
保留历史 per-capture、Wilson 区间和随机子集成功率计算；历史 asr_at_k
不是按 attempt 顺序的 first-k 指标，不能冒充正式 ASR@k。
"""
import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict

from caap.attack.stats import cohort_asr_at_k, wilson_ci


def load_rows(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["success"] = int(r["success"])
        r["attempt"] = int(r["attempt"])
    return rows


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["condition"], r["subject"])].append(r["success"])

    by_cell = defaultdict(list)
    for (model, cond, subject), flags in groups.items():
        by_cell[(model, cond)].append((subject, sum(flags), len(flags)))

    report = {}
    for (model, cond), subjects in sorted(by_cell.items()):
        attempts = {n for _, _, n in subjects}
        if len(attempts) != 1:
            raise SystemExit(f"{model}/{cond}: subjects have different attempt counts {attempts}")
        n = attempts.pop()
        counts = [c for _, c, _ in subjects]
        k = sum(counts)
        total = n * len(counts)
        lo, hi = wilson_ci(k, total)
        # k 大于实际尝试次数时, 无偏的 ASR@k 不可估计, 不把截断后的数冒充成 k=20
        ks = tuple(kk for kk in (1, 5, 20) if kk <= n)
        report[f"{model}|{cond}"] = {
            "n_subjects": len(counts),
            "attempts_per_subject": n,
            "per_capture_asr": round(100 * k / total, 2),
            "ci95": [round(100 * lo, 2), round(100 * hi, 2)],
            "per_subject_successes": {s: c for s, c, _ in subjects},
            "asr_at_k": {str(kk): round(100 * v, 2) for kk, v in cohort_asr_at_k(counts, n, ks).items()},
        }
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=(
        "Legacy diagnostic only: historical random-subset ASR@k, not the v2 physical protocol."))
    p.add_argument("--allow-legacy-protocol", action="store_true",
                   help="acknowledge unverified historical metrics; never use as paper evidence")
    p.add_argument("--csv", required=True)
    p.add_argument("--out", default=None)
    args = p.parse_args(argv)
    if not args.allow_legacy_protocol:
        p.error("--allow-legacy-protocol is required: legacy random-subset ASR is not v2 evidence")
    args.csv = Path(args.csv).expanduser().resolve()
    if not args.csv.is_file():
        p.error(f"--csv must be an existing file: {args.csv}")
    if args.out:
        requested_out = Path(args.out).expanduser()
        if requested_out.is_symlink():
            p.error(f"--out already exists as a symlink: {requested_out}")
        args.out = requested_out.resolve()
        if args.out.exists():
            p.error(f"--out already exists: {args.out}")
        if not args.out.parent.is_dir():
            p.error(f"--out parent directory does not exist: {args.out.parent}")
    report = {
        "schema": "legacy-diagnostic",
        "evidence_type": "unverified",
        "paper_eligible": False,
        "metric_warning": "Historical asr_at_k is random-subset success, not ordered first-k ASR.",
        "results": summarize(load_rows(args.csv)),
    }
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        with args.out.open("x") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
