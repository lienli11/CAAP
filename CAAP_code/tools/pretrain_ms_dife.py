"""在干净掌纹上预训练 MS-DIFE, 再把权重交给 attack.main --ms_dife_ckpt.

论文 IV-E 写的是预训练后冻结. 原仓库没有这一步, 特征提取器是随机初始化的,
身份损失因此没有掌纹语义. 这里用一个线性分类头做监督预训练, 只保存 MS-DIFE 本身.
"""
import argparse
import os
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from attack.modules import MS_DIFE  # noqa: E402
from data.data import PalmPrint  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data_path", required=True)
    p.add_argument("--num_class", type=int, required=True)
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--out", required=True)
    p.add_argument("--norm", default="aug_0.5")
    args = p.parse_args()

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
    torch.save(net.state_dict(), args.out)
    print(f"saved {args.out}  feature_dim={dim}")


if __name__ == "__main__":
    main()
