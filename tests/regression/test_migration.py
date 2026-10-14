"""Migration compatibility checks, not evidence of scientific protocol correctness."""
import hashlib
from importlib.util import find_spec
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MISSING_RESEARCH = tuple(name for name in ("torch", "torchvision", "numpy", "PIL", "tqdm")
                         if find_spec(name) is None)
RESEARCH_SKIP_REASON = "optional research dependencies missing: " + ", ".join(MISSING_RESEARCH)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src"
UPSTREAM = ROOT / ".local" / "upstream" / "CAAP_code"
NETS = ("vgg16", "resnet18", "mobilenetv2", "shufflenetv2", "compnet", "ccnet", "co3net")
MODEL_SHA256 = {
    "ccnet.py": "73dfe03bc420a19c80a6054e8ad1b7f003e91cbfa4991de1968ef950e969b0ba",
    "co3net.py": "39cb598715e41e00dd3af7a5db1e8127d82eaf8e6020680530583db775cb7db8",
    "compnet.py": "d0262c11029a4689e583e52c4222aa47522315873eb3950fa2bb13fafcf3694e",
    "mobilenet_v2.py": "e79463929e15a3e9ede3668629069484358224da141937b12a99d8f70381ae60",
    "resnet.py": "88cf1ec898ae1b54a8cb95f9cdffb69a75bcef8a9a26a1622a644ac8abc84a75",
    "shufflenetv2.py": "514ddc73eb191370dc99e3f40568252f7cfddb45ada6def36a9d27a636405b4d",
    "vgg.py": "a7f4f7dfd69c8af0167823a77531b500a237fd5b6ebdb48a44160caef33ca8eb",
}
ALGORITHM_SHA256 = {
    "losses.py": "6ab90c8509bae56c7266820a9fde63afac8e52b02ccfae7287b0ce5f3e619892",
    "modules.py": "9e731fd59eee87c3fa04bec4603b330ed54e82abccb4b6dfb6138b8baed9e6b3",
    "stats.py": "646cbcce8bce433a8095c145de09e8052be878f1ddcbdc3c09336078c337b191",
    "utils.py": "533dd99a0e79474401e17566b6c430efb120e7f5af83a73ed55984e16dc6cf10",
}


def run_python(code, *args, upstream=False):
    env = dict(os.environ, PYTHONPATH=str(UPSTREAM if upstream else SOURCE),
               PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    with tempfile.TemporaryDirectory() as cwd:
        result = subprocess.run([sys.executable, "-c", code, *args], cwd=cwd, env=env,
                                text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout.strip()


FINGERPRINT = r'''
import hashlib
import json
import sys
from types import SimpleNamespace
import torch

torch.set_num_threads(1)
torch.manual_seed(113)
legacy, name = sys.argv[1:]
if name in ("ASIT", "MS_DIFE"):
    if legacy == "old":
        from attack.modules import ASIT, MS_DIFE
    else:
        from caap.attack.modules import ASIT, MS_DIFE
    net = {"ASIT": ASIT, "MS_DIFE": MS_DIFE}[name]()
else:
    if legacy == "old":
        from utils.net_factory import get_net
    else:
        from caap.utils.net_factory import get_net
    net = get_net(SimpleNamespace(net=name, num_class=3))
net.eval()
net.requires_grad_(False)

def digest(value):
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()

state = [(key, list(value.shape), str(value.dtype), digest(value))
         for key, value in net.state_dict().items()]
x = torch.linspace(-1, 1, 128 * 128).reshape(1, 1, 128, 128).requires_grad_()
initial_asit = None
if name == "ASIT":
    initial_asit = [digest(value) for group in net(x) for value in group.values()]
    # 零初始化头的输入梯度恒为零；固定扰动仅用于测试真实几何/强度前向与非零梯度。
    with torch.no_grad():
        for head in (net.head_rot, net.head_trans, net.head_scale, net.head_gain, net.head_bias):
            head.weight.normal_(mean=0, std=0.005)
y = net(x)
if isinstance(y, tuple):
    y = torch.cat([value.flatten(1) for group in y for value in group.values()], dim=1)
assert torch.isfinite(y).all()
if name not in ("ASIT", "MS_DIFE"):
    assert tuple(y.shape) == (1, 3), y.shape
weights = torch.arange(1, y.numel() + 1, dtype=y.dtype).reshape(y.shape)
grad = torch.autograd.grad((y * weights).sum(), x)[0]
assert torch.isfinite(grad).all()
if name == "ASIT":
    assert torch.count_nonzero(grad) > 0
print(json.dumps({"state": state, "output_shape": list(y.shape), "output": digest(y),
                  "input_gradient": digest(grad), "initial_asit": initial_asit}))
'''


class MigrationImportsTest(unittest.TestCase):
    @unittest.skipIf(find_spec("numpy") is None, "optional dependency missing: numpy (stats import)")
    def test_stats_import_does_not_load_torch(self):
        run_python("import sys; import caap.attack.stats; assert 'torch' not in sys.modules")

    @unittest.skipIf(MISSING_RESEARCH, RESEARCH_SKIP_REASON)
    def test_imports_preserve_cwd_path_and_do_not_probe_gpu(self):
        run_python('''
import importlib, os, sys
import torch
from unittest.mock import patch
cwd, path = os.getcwd(), list(sys.path)
with patch("torch.cuda.is_available", side_effect=AssertionError("import-time GPU probe")):
    for name in ("caap.attack.main", "caap.tools.pretrain_ms_dife",
                 "caap.tools.physical_report", "caap.tools.make_synth_data"):
        importlib.import_module(name)
assert os.getcwd() == cwd
assert sys.path == path
''')

    @unittest.skipIf(MISSING_RESEARCH, RESEARCH_SKIP_REASON)
    def test_lazy_exports_remain_compatible(self):
        run_python('''
from caap import attack
from caap.attack.modules import ASIT
assert attack.ASIT is ASIT
assert set(attack.__all__) == {"CAAP_Attack", "ASIT", "MS_DIFE", "PatchSynthesizer",
    "focal_loss", "cw_like_loss", "identity_loss", "feature_diversity_loss",
    "create_shape_mask", "ssim_loss", "_normalize_for_model", "ASIT_PRESETS"}
try:
    attack.not_an_export
except AttributeError:
    pass
else:
    raise AssertionError("unknown lazy export")
''')


class MigrationBaselineTest(unittest.TestCase):
    def test_model_files_are_byte_identical_to_migration_baseline(self):
        for name, expected in MODEL_SHA256.items():
            with self.subTest(model=name):
                self.assertEqual(hashlib.sha256((SOURCE / "caap" / "models" / name).read_bytes()).hexdigest(), expected)

    def test_math_modules_are_byte_identical_to_migration_baseline(self):
        for name, expected in ALGORITHM_SHA256.items():
            with self.subTest(module=name):
                self.assertEqual(hashlib.sha256((SOURCE / "caap" / "attack" / name).read_bytes()).hexdigest(), expected)

    @unittest.skipIf(MISSING_RESEARCH, RESEARCH_SKIP_REASON)
    def test_stratified_split_and_cross_masks(self):
        run_python('''
from caap.data.data import split_train_val
from caap.attack.utils import create_shape_mask
labels = [0] * 5 + [1] * 3 + [2]
train, val = split_train_val(labels, 0.4, seed=19)
assert (train, val) == split_train_val(labels, 0.4, seed=19)
assert set(train).isdisjoint(val)
assert sorted(train + val) == list(range(len(labels)))
assert all(any(labels[i] == c for i in train) for c in set(labels))
assert [labels[i] for i in val].count(0) == 2
assert [labels[i] for i in val].count(1) == 1
assert create_shape_mask("cross", 30).sum().item() == 459
assert create_shape_mask("cross", 40).sum().item() == 759
''')


def _current_forward(name):
    @unittest.skipIf(MISSING_RESEARCH, RESEARCH_SKIP_REASON)
    def test(self):
        result = json.loads(run_python(FINGERPRINT, "new", name))
        self.assertTrue(result["state"])
        self.assertEqual(result["output_shape"][0], 1)
    return test


def _legacy_comparison(name):
    @unittest.skipIf(MISSING_RESEARCH, RESEARCH_SKIP_REASON)
    def test(self):
        if not (UPSTREAM / "utils" / "net_factory.py").is_file():
            self.skipTest("local upstream unavailable: byte-hash baseline is not old/new numerical proof")
        old = json.loads(run_python(FINGERPRINT, "old", name, upstream=True))
        new = json.loads(run_python(FINGERPRINT, "new", name))
        self.assertEqual(new, old)
    return test


for _name in NETS + ("ASIT", "MS_DIFE"):
    setattr(MigrationBaselineTest, "test_current_forward_and_gradient_" + _name, _current_forward(_name))
    setattr(MigrationBaselineTest, "test_old_new_state_forward_gradient_" + _name, _legacy_comparison(_name))


if __name__ == "__main__":
    unittest.main()
