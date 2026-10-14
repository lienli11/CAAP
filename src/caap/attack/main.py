"""
CAAP Main: Entry point for attack training
"""
import argparse
import json
import os
import time
import math
from pathlib import Path
import numpy as np
import torch
import random

from caap.data.data import get_data
from caap.utils.net_factory import get_net
from caap.attack.attack import CAAP_Attack

def set_seed(seed=42):
    """For reproducibility"""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def _resolve_num_class(dataset: str) -> int:
    """Resolve number of classes for dataset.

    Note: AISEC labels are 1-49, so we need 50 classes (0-49) to match checkpoint.
    """
    dataset = dataset.lower()
    if dataset == "tongji":
        return 600
    if dataset == "iitd":
        return 460
    if dataset == "aisec":
        return 50
    raise ValueError(f"Unsupported dataset: {dataset}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Legacy CAAP diagnostic only; unverified, not the v2 protocol or paper evidence."
    )
    parser.add_argument("--allow-legacy-protocol", action="store_true",
                        help="acknowledge legacy protocol and trusted PIL pickle input")

    # Dataset & Mode
    parser.add_argument("--dataset", type=str, default="tongji",
                        choices=["tongji", "iitd", "aisec"])
    parser.add_argument("--attack_mode", type=str, default="untargeted",
                        choices=["targeted", "untargeted"])
    parser.add_argument("--target_class", type=int, default=0)
    parser.add_argument("--target_bank_size", type=int, default=64)
    parser.add_argument("--data_path", type=str, default=None,
                        help="required explicit trusted legacy PIL .pth path, relative to caller cwd")
    parser.add_argument("--num_class", type=int, default=None)
    parser.add_argument("--val_ratio", type=float, default=0.1,
                        help="per-identity train hold-out; must be strictly between 0 and 1")
    parser.add_argument("--split_seed", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)

    # Training Hyperparams
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=5e-3)
    parser.add_argument("--stn_lr", type=float, default=5e-4)
    parser.add_argument("--early_stop_patience", type=int, default=10)
    parser.add_argument("--grad_accum_steps", type=int, default=1)


    # Loss Weights (lambda_adv is fixed at 1.0)
    parser.add_argument("--lambda_adv", type=float, default=1.0) # Fix lambda_adv to 1.0 (for ablation study control)
    parser.add_argument("--lambda_vis", type=float, default=0.004)
    parser.add_argument("--lambda_id", type=float, default=0.20)
    parser.add_argument("--lambda_tv", type=float, default=2e-5)
    parser.add_argument("--identity_margin", type=float, default=0.5)
    parser.add_argument("--kappa", type=float, default=0.0)

    # Advanced Loss Options
    parser.add_argument("--use_focal_loss", action="store_true")
    parser.add_argument("--focal_gamma", type=float, default=2.0)
    parser.add_argument("--lambda_focal", type=float, default=0.1)
    parser.add_argument("--use_diversity_loss", action="store_true")
    parser.add_argument("--lambda_diversity", type=float, default=0.05)

    # Curriculum Learning
    parser.add_argument("--use_curriculum", action="store_true")
    parser.add_argument("--curriculum_epochs", type=int, default=10)

    # MS-DIFE Training Options
    parser.add_argument("--ms_dife_joint_training", action="store_true")
    parser.add_argument("--ms_dife_lr", type=float, default=1e-5)
    parser.add_argument("--ms_dife_distillation", action="store_true")
    parser.add_argument("--ms_dife_ckpt", type=str, default=None,
                        help="required pretrained MS-DIFE state_dict unless --disable_ms_dife is set")

    # Patch & Image Settings
    parser.add_argument("--patch_size", type=int, default=40)
    parser.add_argument("--patch_shape", type=str, default="cross",
                        choices=["cross", "square", "circle", "triangle", "patch"])
    parser.add_argument("--cross_thickness_ratio", type=float, default=0.25)
    parser.add_argument("--img_size", type=int, default=128)
    parser.add_argument("--input_channels", type=int, default=1)
    parser.add_argument("--norm", type=str, default="aug_0.5")
    parser.add_argument("--loc", type=str, default="center", choices=["center", "topleft"])
    parser.add_argument("--location_strategy", type=str, default=None,
                        choices=["center", "random", "attention", "top_left", "topleft", "center_random"])

    # ASIT Parameter Preset
    parser.add_argument("--preset", type=str, default=None,
                        choices=["conservative", "balanced", "aggressive", "max_asr"])

    parser.add_argument("--disable_asit", action="store_true")
    parser.add_argument("--disable_ms_dife", action="store_true")

    # ASIT Transformation Bounds
    parser.add_argument("--max_rotation_deg", type=float, default=20.0)
    parser.add_argument("--max_rotation", type=float, default=None)
    parser.add_argument("--max_translate_px", type=float, default=15.0)
    parser.add_argument("--max_translate", type=float, default=None)
    parser.add_argument("--max_scale_delta", type=float, default=0.2)
    parser.add_argument("--max_gain_delta", type=float, default=0.3)
    parser.add_argument("--max_bias_delta", type=float, default=0.3)
    parser.add_argument("--max_bias", type=float, default=None)

    # ASIT Ablation Flags
    parser.add_argument("--enable_rotation", action="store_true", default=True)
    parser.add_argument("--no_enable_rotation", action="store_false", dest="enable_rotation")
    parser.add_argument("--enable_translation", action="store_true", default=True)
    parser.add_argument("--no_enable_translation", action="store_false", dest="enable_translation")
    parser.add_argument("--enable_scale", action="store_true", default=True)
    parser.add_argument("--no_enable_scale", action="store_false", dest="enable_scale")
    parser.add_argument("--enable_gain", action="store_true", default=True)
    parser.add_argument("--no_enable_gain", action="store_false", dest="enable_gain")
    parser.add_argument("--enable_bias", action="store_true", default=True)
    parser.add_argument("--no_enable_bias", action="store_false", dest="enable_bias")

    # RaS (EOT) Settings
    parser.add_argument("--use_ras_eot", action="store_true", default=True)
    parser.add_argument("--no_ras_eot", action="store_false", dest="use_ras_eot")
    parser.add_argument("--n_eot_samples", type=int, default=1)
    parser.add_argument("--jitter_brightness", type=float, default=0.25)
    parser.add_argument("--jitter_contrast", type=float, default=0.2)
    parser.add_argument("--noise_std", type=float, default=0.02)
    parser.add_argument("--use_affine_eot", action="store_true", default=False)
    parser.add_argument("--affine_rotation", type=float, default=5.0)
    parser.add_argument("--affine_translate", type=float, default=3.0)

    # Evaluation Settings
    parser.add_argument("--eot_eval", action="store_true")
    parser.add_argument("--eot_eval_samples", type=int, default=10)

    # Misc
    parser.add_argument("--net", type=str, default="compnet")
    parser.add_argument("--model_ckpt", type=str, default=None)
    parser.add_argument("--co3net", action="store_true", default=False)
    parser.add_argument("--grad_clip", type=float, default=1.0)
    parser.add_argument("--disable_scheduler", action="store_true")
    parser.add_argument("--disable_edge_smoothing", action="store_true")
    parser.add_argument("--num_workers", type=int, default=4)
    parser.add_argument("--save_dir", type=str, default="runs/legacy")

    args = parser.parse_args(argv)
    if not args.allow_legacy_protocol:
        parser.error("--allow-legacy-protocol is required: legacy diagnostics are unverified, not paper evidence")
    if not math.isfinite(args.val_ratio) or not 0 < args.val_ratio < 1:
        parser.error("--val_ratio must be finite and strictly between 0 and 1; test-split selection is forbidden")
    # 只有 aug_0.5 的反归一化在旧链路中明确可逆；其他模式需未来正式协议验证后再开放。
    if args.norm != "aug_0.5":
        parser.error("--norm only supports aug_0.5 in the guarded legacy entrypoint")
    for name in ("epochs", "batch_size", "lr", "stn_lr", "grad_accum_steps", "target_bank_size",
                 "patch_size", "img_size", "input_channels", "n_eot_samples", "eot_eval_samples",
                 "ms_dife_lr", "curriculum_epochs", "cross_thickness_ratio"):
        value = getattr(args, name)
        if not math.isfinite(value) or value <= 0:
            parser.error(f"--{name} must be positive and finite")
    for name, value in vars(args).items():
        if isinstance(value, float) and (not math.isfinite(value) or value < 0):
            parser.error(f"--{name} must be nonnegative and finite")
    if args.num_workers < 0:
        parser.error("--num_workers must be nonnegative")
    if args.patch_size > args.img_size:
        parser.error("--patch_size must not exceed --img_size")
    if args.cross_thickness_ratio > 1:
        parser.error("--cross_thickness_ratio must not exceed 1")
    if args.num_class is not None and args.num_class <= 0:
        parser.error("--num_class must be positive")
    args.num_class = args.num_class or _resolve_num_class(args.dataset)
    if not 0 <= args.target_class < args.num_class:
        parser.error("--target_class must be in [0, num_class)")
    if args.net not in ("vgg16", "resnet18", "mobilenetv2", "shufflenetv2", "compnet", "ccnet", "co3net"):
        parser.error("--net must select an existing victim model alias")
    for name in ("data_path", "model_ckpt"):
        value = getattr(args, name)
        if not value:
            parser.error(f"--{name} must be provided; implicit data paths and random victims are forbidden")
        path = Path(value).expanduser().resolve()
        if not path.is_file():
            parser.error(f"--{name} must be an existing file: {path}")
        setattr(args, name, str(path))
    if not args.disable_ms_dife and not args.ms_dife_ckpt:
        parser.error("--ms_dife_ckpt is required unless --disable_ms_dife is specified")
    if args.ms_dife_ckpt:
        path = Path(args.ms_dife_ckpt).expanduser().resolve()
        if not path.is_file():
            parser.error(f"--ms_dife_ckpt must be an existing file: {path}")
        args.ms_dife_ckpt = str(path)
    args.save_dir = str(Path(args.save_dir).expanduser().resolve())
    args.schema = "legacy-diagnostic"
    args.evidence_type = "unverified"
    args.paper_eligible = False

    # ?? 'patch' ??? create_shape_mask ??????; ???? CAAPs ???
    if args.patch_shape == "patch":
        print("WARNING: --patch_shape patch is deprecated and now maps to 'square' (it previously produced a triangle)")
        args.patch_shape = "square"

    # Handle deprecated parameter names
    if args.max_rotation is not None:
        args.max_rotation_deg = args.max_rotation
    if args.max_translate is not None:
        args.max_translate_px = args.max_translate
    if args.max_bias is not None:
        args.max_bias_delta = args.max_bias

    # Create Save Directory
    mode_suffix = f"{args.attack_mode}"
    if args.attack_mode == 'targeted':
        mode_suffix += f"_t{args.target_class}"
    exp_name = f"{args.dataset}_{args.net}_{mode_suffix}_{args.patch_shape}{args.patch_size}_s{args.seed}"
    save_path = os.path.join(args.save_dir, exp_name)
    if os.path.lexists(save_path):
        parser.error(f"experiment directory already exists: {save_path}")
    if os.path.exists(args.save_dir) and not os.path.isdir(args.save_dir):
        parser.error(f"--save_dir must be a directory: {args.save_dir}")
    from torchvision.utils import save_image

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    set_seed(args.seed)
    os.makedirs(save_path, exist_ok=False)
    with open(os.path.join(save_path, "metadata.json"), "x") as f:
        json.dump({"schema": args.schema, "evidence_type": args.evidence_type,
                   "paper_eligible": args.paper_eligible}, f, indent=2)
    print("WARNING: legacy diagnostics only; unverified, not paper-eligible; trusted pickle data only")

    # --- 1. Load Data & Model ---
    print("=" * 80)
    print(f"?? CAAP: Grayscale Radiometric Adaptive Spatial Patch Attack")
    print(f"   Dataset: {args.dataset}")
    print(f"   Model: {args.net}")
    print(f"   Attack Mode: {args.attack_mode}")
    if args.attack_mode == 'targeted':
        print(f"   Target Class: {args.target_class}")
    print(f"   Patch Size: {args.patch_size}x{args.patch_size}")
    print(f"   Patch Shape: {args.patch_shape}")
    print(f"   ?_vis={args.lambda_vis}, ?_id={args.lambda_id}, ?_tv={args.lambda_tv}")
    print("=" * 80)

    trainloader, valloader, testloader = get_data(args)
    args.trainloader = trainloader
    args.valloader = valloader
    args.testloader = testloader

    # Infer image size and channels
    dataset = getattr(trainloader, "dataset", None)
    if dataset is not None:
        args.img_size = getattr(dataset, "imside", args.img_size)
        args.input_channels = getattr(dataset, "chs", getattr(dataset, "outchannels", args.input_channels))

    print(f"\n?? Data loaded: {len(trainloader)} train batches, {len(testloader)} test batches")
    print(f"   Image size: {args.img_size}x{args.img_size}, Channels: {args.input_channels}")

    # Load target model
    model = get_net(args).to(device)
    print(f"Loading required victim checkpoint: {args.model_ckpt}")
    state = torch.load(args.model_ckpt, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    print(f"? Target model {args.net} loaded and FROZEN")

    # --- 2. Initialize Attacker ---
    attacker = CAAP_Attack(model, args, device)
    print(f"   ? Effective mask area: {attacker.mask_area:.0f} px (fill={attacker.mask_fill_ratio:.3f})")


    # -1 ???? epoch ????, ?? ASR ?? 0 ?????????
    best_asr = -1.0
    best_epoch = 0
    epochs_no_improve = 0
    patience = args.early_stop_patience

    # --- 3. Training Loop ---
    print(f"\n?? Start Training for {args.epochs} epochs (patience={patience})...")
    training_start = time.time()

    for epoch in range(args.epochs):
        epoch_start = time.time()

        # Train
        loss_avg, atk_loss_avg, kept, total = attacker.train_epoch(epoch + 1)

        # ??????????, ??????????????
        if args.eot_eval:
            asr, eval_total = attacker.evaluate_with_eot(args.valloader, n_samples=args.eot_eval_samples)
        else:
            asr, eval_total, _ = attacker.evaluate(args.valloader)

        epoch_time = time.time() - epoch_start

        # Logging
        mode_label = "Target Success" if args.attack_mode == 'targeted' else "ASR"
        eval_method = f"(EOTx{args.eot_eval_samples})" if args.eot_eval else ""
        print(f"\n?? Epoch {epoch+1}/{args.epochs} | Time: {epoch_time:.1f}s")
        print(f"   Loss: {loss_avg:.4f} | AtkLoss: {atk_loss_avg:.4f}")
        print(f"   Val {mode_label}{eval_method}: {asr:.2f}% ({eval_total} samples)")
        print(f"   Correctly classified samples used: {kept}/{total}")

       
        # Save Best
        if asr > best_asr:
            best_asr = asr
            best_epoch = epoch + 1
            epochs_no_improve = 0
            print(f"   ? New Best {mode_label}: {best_asr:.2f}%! Saving...")

            # Save Patch
            torch.save(attacker.patch.data, os.path.join(save_path, "best_patch.pth"))
            save_image(attacker.patch.data, os.path.join(save_path, "best_patch.png"))

            # Save ASIT Model
            if attacker.use_asit:
                torch.save(attacker.asit.state_dict(), os.path.join(save_path, "best_asit.pth"))

            # Save visualization
            with torch.no_grad():
                for images, labels in args.valloader:
                    if args.co3net and isinstance(images, list):
                        images = images[0]
                    images = images.to(device)[:8]

                    if attacker.use_asit:
                        theta, intensity = attacker.asit(images)
                    else:
                        theta, intensity = None, None

                    # Denormalize for patch synthesis / visualization
                    if args.norm == 'aug_0.5':
                        images_vis = images * 0.5 + 0.5
                    else:
                        images_vis = images

                    loc = args.loc
                    demo_adv, demo_mask = attacker.synthesizer.synthesize_attack(
                        images_vis, theta, intensity, attacker.patch, attacker.patch_mask,
                        attacker.patch_size, canvas_loc=loc
                    )

                    # Stack: original | mask | adversarial
                    n_channels = images_vis.size(1)
                    if n_channels == 1:
                        vis_mask = demo_mask
                    else:
                        vis_mask = demo_mask.repeat(1, n_channels, 1, 1)

                    save_image(
                        torch.cat([images_vis, vis_mask, demo_adv], dim=0),
                        os.path.join(save_path, f"vis_epoch_{epoch+1}.png"),
                        nrow=8
                    )
                    break
        else:
            epochs_no_improve += 1
            if patience > 0 and epochs_no_improve >= patience:
                print(f"\n?? Early stopping triggered (no improvement for {patience} epochs)")
                break

    # Training complete. Reload the val-selected patch and score the test split once.
    total_time = time.time() - training_start
    from caap.attack.stats import wilson_ci

    attacker.patch.data.copy_(torch.load(os.path.join(save_path, "best_patch.pth"), map_location=device, weights_only=True))
    if attacker.use_asit:
        attacker.asit.load_state_dict(torch.load(os.path.join(save_path, "best_asit.pth"), map_location=device, weights_only=True))

    test_asr, test_total, test_k = attacker.evaluate(args.testloader, mode="oracle")
    deploy_asr, deploy_n, deploy_k = attacker.evaluate(args.testloader, mode="deploy")
    robust = attacker.robustness_report(args.testloader, mode="deploy")

    def _ci(k, n):
        lo, hi = wilson_ci(k, n)
        return [round(100 * lo, 2), round(100 * hi, 2)]

    print(f"\n{'='*80}")
    print(f"Training complete in {total_time/60:.1f} min")
    print(f"   Best val {mode_label}: {best_asr:.2f}% (epoch {best_epoch})")
    print(f"   Test oracle {mode_label}: {test_asr:.2f}% (n={test_total}, 95% CI {_ci(test_k, test_total)})")
    print(f"   Test deploy {mode_label}: {deploy_asr:.2f}% (n={deploy_n}, 95% CI {_ci(deploy_k, deploy_n)})")
    for deg_name, row in robust.items():
        print(f"   Deploy+{deg_name}: {row['asr']:.2f}% (n={row['n']})")
    print(f"Results saved to: {save_path}")
    print(f"{'='*80}")

    # Save final metrics
    final_metrics = {
        "schema": "legacy-diagnostic",
        "evidence_type": "unverified",
        "paper_eligible": False,
        "val_asr": best_asr,
        "test_asr_oracle": test_asr,
        "test_oracle_ci95": _ci(test_k, test_total),
        "test_denominator": test_total,
        "test_asr_deploy": deploy_asr,
        "test_deploy_ci95": _ci(deploy_k, deploy_n),
        "deploy_robustness": {k: {"asr": v["asr"], "n": v["n"], "ci95": _ci(v["k"], v["n"])} for k, v in robust.items()},
        "best_epoch": best_epoch,
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "total_epochs": epoch + 1,
        "attack_mode": args.attack_mode,
        "target_class": args.target_class if args.attack_mode == 'targeted' else None,
        "dataset": args.dataset,
        "net": args.net,
        "patch_size": args.patch_size,
        "patch_shape": attacker.patch_shape,
        "mask_area": attacker.mask_area,
        "mask_fill_ratio": attacker.mask_fill_ratio,
        "location_strategy": attacker.location_strategy,
        "lambda_adv": args.lambda_adv,
        "lambda_vis": args.lambda_vis,
        "lambda_id": args.lambda_id,
        "lambda_tv": args.lambda_tv,
        "total_time_minutes": total_time / 60,
    }
    with open(os.path.join(save_path, "metrics.json"), "w") as f:
        json.dump(final_metrics, f, indent=2)

    config = {k: v for k, v in vars(args).items() if not k.endswith("loader")}
    with open(os.path.join(save_path, "config.json"), "w") as f:
        json.dump(config, f, indent=2, default=str)


if __name__ == "__main__":
    main()
