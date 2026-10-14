"""把物理拍摄记录收成审稿人要的口径.

CSV 列: subject, attempt, success, condition, model
success 为 0/1, attempt 从 1 计. 每个 (model, condition, subject) 的尝试次数必须相同.

输出:
- per-capture ASR 及 95% Wilson 区间 (主指标)
- 每个受试者的成功次数
- ASR@k, k=1,5,20. k=20 才对应原稿 "20 次里至少成功 1 次"
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attack.stats import cohort_asr_at_k, wilson_ci  # noqa: E402


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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--out", default=None)
    args = p.parse_args()
    report = summarize(load_rows(args.csv))
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
