"""生成合成掌纹数据, 并把受害模型训练到可用精度, 用于在无真实数据时冒烟验证代码改动.

只验证代码路径是否走通, 产生的任何数值都不能写进论文.
"""
import argparse
import os
import sys

import torch
import torch.nn.functional as F

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "..", "CAAP_code"))

from data.data import PalmPrint  # noqa: E402
from utils.net_factory import get_net  # noqa: E402

ARC_NETS = {"compnet", "ccnet", "co3net"}


def make_split(num_class, per_class, size=128, seed=0):
    """每个身份一组固定的正弦条纹纹理(模拟掌纹主线方向) + 逐样本噪声."""
    from PIL import Image

    g = torch.Generator().manual_seed(seed)
    yy, xx = torch.meshgrid(torch.linspace(0, 1, size), torch.linspace(0, 1, size), indexing="ij")
    images, labels = [], []
    for c in range(num_class):
        gc = torch.Generator().manual_seed(1000 + c)
        freq = 4 + 12 * torch.rand(3, generator=gc)
        phase = 2 * torch.pi * torch.rand(3, generator=gc)
        theta = torch.pi * torch.rand(3, generator=gc)
        base = torch.zeros(size, size)
        for k in range(3):
            proj = xx * torch.cos(theta[k]) + yy * torch.sin(theta[k])
            base = base + torch.sin(2 * torch.pi * freq[k] * proj + phase[k])
        base = (base - base.min()) / (base.max() - base.min() + 1e-8)
        for _ in range(per_class):
            img = (base + 0.05 * torch.randn(size, size, generator=g)).clamp(0, 1)
            images.append(Image.fromarray((img * 255).to(torch.uint8).numpy(), mode="L"))
            labels.append(c)
    return {"images": images, "labels": labels}


def train_victim(net_name, pth, num_class, epochs):
    class _A:
        pass

    a = _A()
    a.net, a.num_class = net_name, num_class
    net = get_net(a)
    ds = PalmPrint(data_dir=pth, norm="aug_0.5", train=True, co3net=False)
    dl = torch.utils.data.DataLoader(ds, batch_size=16, shuffle=True)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for _ in range(epochs):
        net.train()
        for x, y in dl:
            logits = net(x, y) if net_name in ARC_NETS else net(x)
            loss = F.cross_entropy(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval()
    test = PalmPrint(data_dir=pth, norm="aug_0.5", train=False, co3net=False)
    correct = 0
    with torch.no_grad():
        for x, y in torch.utils.data.DataLoader(test, batch_size=32):
            correct += (net(x).argmax(1) == y).sum().item()
    return net, correct / len(test)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--nets", nargs="+", default=["compnet", "resnet18"])
    p.add_argument("--num_class", type=int, default=8)
    p.add_argument("--epochs", type=int, default=15)
    args = p.parse_args()

    torch.manual_seed(0)
    out = os.path.join(ROOT, "synth")
    os.makedirs(os.path.join(out, "data_pth"), exist_ok=True)
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)

    pth = os.path.join(out, "data_pth", "synth_128.pth")
    torch.save({"train": make_split(args.num_class, 10, seed=0),
                "test": make_split(args.num_class, 5, seed=1)}, pth)
    print(f"[data] {pth}")

    for name in args.nets:
        net, acc = train_victim(name, pth, args.num_class, args.epochs)
        ck = os.path.join(out, "ckpt", f"{name}.pth")
        torch.save(net.state_dict(), ck)
        print(f"[ckpt] {name}: clean test acc = {acc:.3f} -> {ck}")


if __name__ == "__main__":
    main()
