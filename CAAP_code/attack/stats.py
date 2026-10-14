"""评测统计(仅依赖 numpy).

数字 ASR、物理重试预算和验证指标共用这一处, 避免各脚本各写一套口径.
"""
import math

import numpy as np


def wilson_ci(k, n, z=1.96):
    """二项比例的 Wilson 区间. n=0 时返回 (0, 1)."""
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def asr_at_k(successes, attempts, k):
    """一名受试者 attempts 次里成功 successes 次时, 允许重试 k 次至少成功一次的无偏估计.

    1 - C(attempts-successes, k) / C(attempts, k). k=1 就是单次成功率.
    """
    if attempts <= 0 or k <= 0:
        return 0.0
    k = min(k, attempts)
    if successes <= 0:
        return 0.0
    if attempts - successes < k:
        return 1.0
    return 1.0 - math.comb(attempts - successes, k) / math.comb(attempts, k)


def cohort_asr_at_k(per_subject_successes, attempts, ks):
    """对一组受试者取 asr_at_k 的均值. 返回 {k: mean}."""
    out = {}
    for k in ks:
        vals = [asr_at_k(c, attempts, k) for c in per_subject_successes]
        out[int(k)] = float(np.mean(vals)) if vals else 0.0
    return out


def pairwise_scores(embeddings, labels):
    """L2 归一化嵌入上的 genuine / impostor 余弦分数(上三角, 不含自身)."""
    emb = np.asarray(embeddings, dtype=np.float64)
    labels = np.asarray(labels)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    emb = emb / np.clip(norms, 1e-12, None)
    sim = emb @ emb.T
    genuine, impostor = [], []
    n = len(labels)
    for i in range(n):
        same = labels[i + 1:] == labels[i]
        row = sim[i, i + 1:]
        genuine.extend(row[same].tolist())
        impostor.extend(row[~same].tolist())
    return np.asarray(genuine), np.asarray(impostor)


def verification_operating_points(genuine, impostor, fars=(1e-2, 1e-3)):
    """给定分数, 返回 EER 以及若干 FAR 工作点上的 FRR.

    决策规则: 分数 >= 阈值判为接受. EER 取 |FAR-FRR| 最小处二者的平均.
    """
    genuine = np.asarray(genuine, dtype=np.float64)
    impostor = np.asarray(impostor, dtype=np.float64)
    if len(genuine) == 0 or len(impostor) == 0:
        return {"eer": None, "frr_at_far": {}}

    thresholds = np.unique(np.concatenate([genuine, impostor]))
    best_gap, best_far, best_frr = None, None, None
    curve = []
    for t in thresholds:
        far = float(np.mean(impostor >= t))
        frr = float(np.mean(genuine < t))
        curve.append((far, frr, float(t)))
        gap = abs(far - frr)
        if best_gap is None or gap < best_gap:
            best_gap, best_far, best_frr = gap, far, frr

    frr_at = {}
    for target in fars:
        # 取 FAR 不超过 target 时 FRR 最小的点; 达不到则记 None
        feasible = [frr for far, frr, _ in curve if far <= target + 1e-12]
        frr_at[target] = float(min(feasible)) if feasible else None

    return {
        "eer": float((best_far + best_frr) / 2.0),
        "frr_at_far": frr_at,
        "n_genuine": int(len(genuine)),
        "n_impostor": int(len(impostor)),
    }
