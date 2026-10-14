"""在干净掌纹上预训练 MS-DIFE, 再把权重交给 attack.main --ms_dife_ckpt.

论文 IV-E 写的是预训练后冻结. 原仓库没有这一步, 特征提取器是随机初始化的,
身份损失因此没有掌纹语义. 这里用一个线性分类头做监督预训练, 只保存 MS-DIFE 本身.
"""
import argparse
import json
import math
import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from caap.attack.modules import MS_DIFE
from caap.data.data import PalmPrint


def main(argv=None):
    p = argparse.ArgumentParser(description=(
        "Legacy full-train MS-DIFE pretraining only; this is not the v2 train/validation protocol."))
    p.add_argument("--allow-legacy-protocol", action="store_true",
                   help="acknowledge full-train legacy behavior and trusted pickle input")
    p.add_argument("--data_path", required=True, help="trusted legacy PIL .pth dataset only")
    p.add_argument("--num_class", type=int, required=True)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", required=True)
    p.add_argument("--norm", default="aug_0.5", choices=["aug_0.5"])
    args = p.parse_args(argv)
    if not args.allow_legacy_protocol:
        p.error("--allow-legacy-protocol is required: legacy full-train pretraining is not v2")
    for name in ("num_class", "epochs", "batch_size", "lr"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            p.error(f"--{name} must be positive and finite")
    args.data_path = str(Path(args.data_path).expanduser().resolve())
    if not Path(args.data_path).is_file():
        p.error(f"--data_path must be an existing file: {args.data_path}")
    requested_out = Path(args.out).expanduser()
    if requested_out.is_symlink():
        p.error(f"--out already exists as a symlink: {requested_out}")
    args.out = str(requested_out.resolve())
    metadata_path = Path(args.out + ".metadata.json")
    if Path(args.out).exists() or metadata_path.exists() or metadata_path.is_symlink():
        p.error(f"--out or its metadata already exists: {args.out}")
    print("WARNING: legacy full-train pretraining; unverified, not paper-eligible; trusted pickle input only")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds = PalmPrint(data_dir=args.data_path, norm=args.norm, train=True, co3net=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=0)

    net = MS_DIFE(in_channels=1).to(device)
    with torch.no_grad():
        dim = net(torch.zeros(1, 1, 128, 128, device=device)).size(1)
    head = nn.Linear(dim, args.num_class).to(device)
    opt = torch.optim.Adam(list(net.parameters()) + list(head.parameters()), lr=args.lr)

    for epoch in range(args.epochs):
        net.train()
        total, correct, n = 0.0, 0, 0
        for images, labels in loader:
            if args.norm == "aug_0.5":
                images = images * 0.5 + 0.5
            images, labels = images.to(device), labels.to(device)
            logits = head(net(images))
            loss = F.cross_entropy(logits, labels)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item() * labels.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            n += labels.size(0)
        print(f"epoch {epoch+1}/{args.epochs}  loss={total/max(n,1):.4f}  train_acc={100*correct/max(n,1):.1f}%")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "xb") as f:
        torch.save(net.state_dict(), f)
    metadata = {
        "schema": "legacy-diagnostic", "evidence_type": "unverified", "paper_eligible": False,
        "protocol": "legacy-full-train-pretraining", "feature_dim": dim,
    }
    with metadata_path.open("x", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"saved {args.out}  feature_dim={dim}")


if __name__ == "__main__":
    main()
